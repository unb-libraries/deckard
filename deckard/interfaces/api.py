import socket
import signal
import sys

from filelock import FileLock
from flask import Flask, Response, g, request
from logging import Logger
from threading import Lock
from waitress import serve as waitress_serve

from deckard.core import get_logger, json_dumper, list_of_dicts_to_dict, get_api_gpu_exclusive_mode
from deckard.core.builders import build_llm_chains, build_rag_stacks
from deckard.core.config import get_api_host, get_api_llm_config, get_api_port, get_gpu_lockfile
from deckard.core.time import cur_timestamp, TimingManager
from deckard.core.utils import report_memory_use
from deckard.llm import LLM, LLMQuery, ResponseVerifier, MaliciousClassifier, CompoundClassifier, CompoundResponseSummarizer, ResponseSourceExtractor, fail_response
from deckard.interfaces.services import build_qa_stacks, query_qa_stack
from deckard.response import ApiResponse

DECKARD_CMD_STRING = 'api:start'

app = Flask(__name__)

gpu_lock = FileLock(get_gpu_lockfile())
query_lock = Lock()

gpu_exclusive = get_api_gpu_exclusive_mode()
logger = get_logger()

qa_stacks = None
stacks = None
llm = None
chains = None
timings = TimingManager()

@app.before_request
def before_request():
    """Set the start time for the request."""
    g.start = cur_timestamp()


# Cheery default.
@app.route("/")
def hello():
    """Default endpoint."""
    return "Endpoint Disabled."


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    response = {
        "status": "healthy",
        "message": "Service is running"
    }
    return Response(json_dumper(response, pretty=False), status=200, mimetype='application/json')


@app.route("/query/raw", methods=['POST'])
def rawquery():
    """Direct LLM query. Not logged or for general use."""
    global stacks, llm, chains, timings

    data = request.json
    context = data.get('context')
    query = data.get('query')
    logger.info("Raw LLM Query Recieved with context %s and query %s...", context, query)

    query_lock_type = get_query_lock_type()
    logger.info(f"Waiting for {query_lock_type} lock...")
    with get_query_lock():
        logger.info(f"{query_lock_type} lock acquired.")

        if not gpu_exclusive:
            llm = LLM(logger, get_api_llm_config()).get()
            logger.info("Building LLM Chains...")
            chains = build_llm_chains(llm)
            
        chain = chains['chain-context-plus']
        chain_reponse = chain.invoke(
            {
                "context": context,
                "query": query
            }
        )
        return {
            "response": chain_reponse
        }


# RAG query endpoint.
@app.route("/query/v1", methods=['POST'])
def libpages_query():
    """RAG query endpoint."""
    global stacks, qa_stacks, llm, chains, timings

    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')

    if not gpu_exclusive:
        timings.reset_timing()
    else:
        timings.reset_timing(
            keep_ids=[
                'qa_stacks_build_time',
                'rag_stack_build_time',
                'llm_model_load_time',
                'chain_build_time',
            ]
        )

    # Inits
    response = ApiResponse.new(
        query=query_value,
        pipeline=pipeline,
        exclusive_mode=gpu_exclusive,
        timings=timings,
        logger=logger
    )
    response_was_summarized = False
    query_lock_type = get_query_lock_type()
    logger.info(f"Waiting for {query_lock_type} lock...")
    response.start_timing(['query_lock_wait_time'])

    with get_query_lock():
        response.finalize_timing(['query_lock_wait_time'])
        logger.info(f"{query_lock_type} lock acquired.")

        if not gpu_exclusive:
            with response.time_block('qa_stacks_build_time'):
                qa_stacks = build_qa_stacks(logger, response.timings)

            with response.time_block('rag_stack_build_time'):
                stacks = build_rag_stacks(logger)

            with response.time_block('llm_model_load_time'):
                logger.info("Loading LLM Model...")
                llm = LLM(logger, get_api_llm_config()).get()

            with response.time_block('Chain_build_time'):
                logger.info("Building Query Chains...")
                chains = build_llm_chains(llm)

        stack = stacks[pipeline]
        qa_stack = qa_stacks[pipeline]
        llm_inferences = []
        answer_data = {}
        qa_answered = False
        is_answer = False

        # QA Search, Avoid RAG Stack if Possible
        if qa_stack.has_questions():
            with response.time_block('qa_query_time'):
                qa_response, source_urls = query_qa_stack(qa_stack, query_value, chains, logger)
            response.update({'qa_response': qa_response, 'qa_response_metadata': qa_response['metadata']})

            if qa_response['has_response']:
                logger.info("QA Stack has answer...")
                qa_answered = True
                is_answer = True
                response.update({
                    'response': qa_response['response'],
                    'is_answer': True,
                    'qa_response_used': True,
                    'qa_response_metadata': qa_response['metadata'],
                    'sources_found': True,
                    'sources_reason': "QA Stack",
                    'source_urls': source_urls
                })
            else:
                logger.info("QA Stack has no answer...")
                response.update({
                    'qa_response_used': False,
                    'qa_response_metadata': qa_response['metadata']
                })
        else:
            logger.info("QA stack has no questions...")
            response.update({'qa_response_used': False})

        if not qa_answered:
            # Malicious Classification
            with response.time_block('malicious_query_classification_time'):
                logger.info("Classifying Maliciousness...")
                malicious_classifier = MaliciousClassifier(query_value, chains['malicious'], logger)
                classification, reason, classification_data = malicious_classifier.question_has_malicious_intent()
            response.update({
                'malicious_query_classification': classification,
                'malicious_query_classification_reason': reason,
                'malicious_query_classification_response': classification_data
            })

            if classification != 'Safe':
                logger.info("Classification: Not Safe...")
                response.update({
                    'response': fail_response(),
                    'not_answer_reason': classification_data.get('reason')
                })

            else:
                logger.info("Classification: Safe...")

                # Build LLM Query
                with response.time_block('query_build_time'):
                    logger.info("Building LLM Query Object...")
                    llm_query = LLMQuery(response.response['id'], stack, pipeline, data.get('client'), get_api_llm_config(), logger)

                # Compound Query Extraction
                with response.time_block('compound_query_classification_time'):
                    logger.info("Classifying Compound Query...")
                    compound_classifier = CompoundClassifier(query_value, chains['compound'], logger)
                    classified_compounds, classifier_response, reason = compound_classifier.explode_query()

                if not classified_compounds or 'queries' not in classified_compounds or not classified_compounds['queries']:
                    logger.info("Compound Classification Failed...")
                    response.update({
                        'compound_query_classification_response': classifier_response,
                        'compound_query_classification_success': False,
                        'compound_query_classification_reason': reason
                    })
                    queries_to_infer = {'1': query_value}
                else:
                    logger.info("Compound Classification Succeeded...")
                    response.update({
                        'compound_query_classification_response': classifier_response,
                        'compound_query_classification': classified_compounds,
                        'compound_query_classification_success': True
                    })
                    queries_to_infer = classified_compounds['queries']

                response.update({'queries_to_infer': queries_to_infer})

                # Iterate through all queries to infer
                with response.compound_time_block('llm_query_time'):
                    for query_value in queries_to_infer.values():
                        constructed_query = construct_given_that_query(llm_inferences, query_value)

                        # Query LLM
                        logger.info("Querying LLM...")
                        llm_response = llm_query.query(constructed_query, chains['chain-context-only'])
                        response.update(llm_response)

                        # Response Validity
                        logger.info("Determining if response answers question...")
                        response_value = response.response['response']
                        verifier = ResponseVerifier(constructed_query, response_value, chains['chain-verify-response'], logger)
                        is_answer, reason, answer_data = verifier.response_answers_question()
                        llm_inferences.append({
                            'query': query_value,
                            'constructed_query': constructed_query,
                            'response': response_value,
                            'is_answer': is_answer,
                            'not_answer_reason': None if is_answer else reason,
                            'answer_data': answer_data,
                            'chunks_used': response.response['metadata']['contextbuilder']['chunks_used']
                        })
                        response.timings.increment_compound_timing('llm_query_time')

            with response.time_block('summarizer_query_time'):
                response_summarizer = CompoundResponseSummarizer(chains['summarizer'], logger)
                final_response, response_was_summarized, has_valid_answers = response_summarizer.summarize(llm_inferences)
                response.update({'source_urls': []})

            if has_valid_answers:
                with response.time_block('sources_query_time'):
                    chunks_used = []
                    for inference in llm_inferences:
                        chunks_used.extend(inference['chunks_used'])
                    response_sources = ResponseSourceExtractor(chains['sources'], logger)
                    sources_found, sources_reason, source_urls = response_sources.get_sources(query_value, final_response, chunks_used)
                    response.update({
                        'sources_found': sources_found,
                        'sources_reason': sources_reason,
                        'source_urls': source_urls['source_urls']
                    })

            response.update({
                'query': data.get('query'),
                'response': final_response,
                'is_answer': has_valid_answers,
                'inference_results': list_of_dicts_to_dict(llm_inferences)
            })

    response.update({
        'qa_answered': qa_answered,
        'query_lock_type': query_lock_type,
        'response_was_summarized': response_was_summarized,
    })

    return response.render()


@app.route("/search", methods=['POST'])
def db_search_query():
    """Search RAG embeddings. Not logged or for general use."""
    global stacks, llm, chains, timings

    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')

    logger.info("Embedding Search Recieved: query='%s...", query_value)

    query_lock_type = get_query_lock_type()
    logger.info(f"Waiting for {query_lock_type} lock...")

    with get_query_lock():
        logger.info(f"{query_lock_type}.")

        if not gpu_exclusive:
            logger.info("Building Query Stacks...")
            stacks = build_rag_stacks(logger)            

        stack = stacks[pipeline]
        logger.info("Searching embeddings...")
        response = stack.search(query_value).to_dict()

    if 'error' in response:
        logger.error("Error searching RAG embeddings:")
        logger.error(response['error'])
        return Response(json_dumper(response, pretty=False), status=500, mimetype='application/json')    

    return Response(json_dumper(response, pretty=False), status=200, mimetype='application/json')


# API Start-up.
def start() -> None:
    """Starts the API server."""
    global stacks, qa_stacks, llm, chains, timings
    report_memory_use(logger)
    logger.info("Starting API server...")

    if gpu_exclusive:
        with timings.time_block('query_lock_wait_time'):
            logger.info("Acquiring GPU lock...")
            gpu_lock.acquire()
            logger.info("GPU lock acquired.")

        signal.signal(signal.SIGINT, release_gpu_lock_and_exit)

        with timings.time_block('qa_stacks_build_time'):
            qa_stacks = build_qa_stacks(logger)

        with timings.time_block('rag_stack_build_time'):
            # @TODO: Move to RAG query service.
            logger.info("Building Rag Stacks...")
            stacks = build_rag_stacks(logger)

        with timings.time_block('llm_model_load_time'):
            # @TODO: Move to inference 'provider'.
            logger.info("Loading LLM Model...")
            llm = LLM(logger, get_api_llm_config()).get()

        with timings.time_block('chain_build_time'):
            # @TODO: Move to inference 'provider'.
            logger.info("Building Query Chains...")
            chains = build_llm_chains(llm)

    try:
        waitress_serve(app, host=get_api_host(), port=get_api_port())
    finally:
        if gpu_exclusive:
            logger.info("Releasing GPU lock...")
            gpu_lock.release()
            logger.info("GPU lock released.")

def check_api_server_exit(log: Logger):
    """Exits if the API server is not running.

    Args:
        log (Logger): The logger to use.
    """
    if not api_server_up():
        log.error("API server not running")
        sys.exit(1)

def api_server_up() -> bool:
    """Checks if the API server is running.

    Returns:
        bool: True if the API server is running, False otherwise.
    """
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = (get_api_host(), get_api_port())
    return a_socket.connect_ex(location) == 0

def construct_given_that_query(history: list, new_query: str) -> str:
    """
    Constructs a contextual query using previous interactions.

    Args:
        history (list): A list of dictionaries with keys 'query', 'response', and 'is_answer'.
        new_query (str): The new query to construct with context.

    Returns:
        str: A constructed query using "Given that" statements.
    """
    if not history:
        return new_query  # No prior context, return the query as is

    given_statements = [
        f"Given that {entry['response']}" 
        for entry in history if entry.get('is_answer', True)
    ]

    if not given_statements:
        return new_query  # No valid prior context, return the new query as is

    context_intro = " and ".join(given_statements)

    return f"{context_intro}, {new_query}"  # Form the final structured query

def get_query_lock():
    """Returns the appropriate lock based on the gpu_exclusive mode."""
    if gpu_exclusive:
        return query_lock
    else:
        return gpu_lock

def get_query_lock_type():
    """Returns the appropriate lock type based on the gpu_exclusive mode."""
    if gpu_exclusive:
        return 'Thread'
    else:
        return 'GPU'

def release_gpu_lock_and_exit(signum, frame):
    if gpu_exclusive:
        logger.info("Releasing GPU lock...")
        gpu_lock.release()
        logger.info("GPU lock released.")
    sys.exit(0)
