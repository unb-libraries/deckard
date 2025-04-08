import socket
import signal
import sys

from filelock import FileLock
from flask import Flask, Response, g, request
from logging import Logger
from os import makedirs
from threading import Lock
from waitress import serve as waitress_serve

from deckard.core import get_logger, json_dumper, load_class, list_of_dicts_to_dict, get_api_gpu_exclusive_mode
from deckard.core.builders import build_llm_chains, build_rag_stacks
from deckard.core.config import get_api_host, get_api_llm_config, get_api_port, get_data_dir, get_gpu_lockfile, get_rag_pipeline
from deckard.core.time import cur_timestamp, time_since
from deckard.core.utils import report_memory_use, gen_uuid
from deckard.llm import LLM, LLMQuery, ResponseVerifier, MaliciousClassifier, CompoundClassifier, CompoundResponseSummarizer, ResponseSourceExtractor, fail_response

DECKARD_CMD_STRING = 'api:start'

app = Flask(__name__)

gpu_lock = FileLock(get_gpu_lockfile())
query_lock = Lock()

gpu_exclusive = get_api_gpu_exclusive_mode()
logger = get_logger()

stacks = None
llm = None
chains = None

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
    global stacks, llm, chains

    data = request.json
    context = data.get('context')
    query = data.get('query')
    logger.info("Raw LLM Query Recieved with context %s and query %s...", context, query)

    query_lock_type = get_query_lock_type()
    logger.info(f"Waiting for {query_lock_type} lock...")
    query_lock_start = cur_timestamp()
    with get_query_lock():
        query_lock_wait_time = time_since(query_lock_start)
        logger.info(f"{query_lock_type} lock acquired after {query_lock_wait_time} seconds.")

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
    global stacks, llm, chains

    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')
    response = {
        'id': gen_uuid(),
        'query': query_value,
        'pipeline': pipeline,
        'exclusive_mode': gpu_exclusive
    }

    # Inits
    chain_build_time = 0
    llm_model_load_time = 0
    llm_query_time = 0
    malicious_query_classification_time = 0
    query_build_time = 0
    rag_stack_build_time = 0
    reason_query_time = 0

    query_lock_type = get_query_lock_type()
    logger.info(f"Waiting for {query_lock_type} lock...")
    query_lock_start = cur_timestamp()

    with get_query_lock():
        query_lock_wait_time = time_since(query_lock_start)
        logger.info(f"{query_lock_type} lock acquired after {query_lock_wait_time} seconds.")

        if not gpu_exclusive:
            logger.info("Building Query Stacks...")
            rag_stack_build_start = cur_timestamp()
            stacks = build_rag_stacks(logger)
            rag_stack_build_time = time_since(rag_stack_build_start)

            logger.info("Loading LLM Model...")
            llm_model_load_start = cur_timestamp()
            llm = LLM(logger, get_api_llm_config()).get()
            llm_model_load_time = time_since(llm_model_load_start)

            logger.info("Building Query Chains...")
            chain_build_start = cur_timestamp()
            chains = build_llm_chains(llm)
            chain_build_time = time_since(chain_build_start)

        stack = stacks[pipeline]
        llm_inferences = []
        answer_data = {}
        is_answer = False

        # Malicious Classification
        logger.info("Classifying Maliciousness...")
        is_malicious_start = cur_timestamp()
        malicious_classifier = MaliciousClassifier(query_value, chains['malicious'], logger)
        classification, reason, classification_data = malicious_classifier.question_has_malicious_intent()
        malicious_query_classification_time = time_since(is_malicious_start)
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
            times = {
                'model_load_time': llm_model_load_time,
                'chain_build_time': chain_build_time,
                'query_lock_type': query_lock_type,
                'query_lock_wait_time': query_lock_wait_time,
                'rag_stack_build_time': rag_stack_build_time,
                'query_build_time': 0,
                'malicious_query_classification_time': malicious_query_classification_time,
                'inference_time': 0,
                'reason_query_time': 0,
                'postprocess_time': 0
            }
        else:
            logger.info("Classification: Safe...")

            # Build Query
            logger.info("Building LLM Object...")
            query_build_start = cur_timestamp()
            llm_query = LLMQuery(response['id'], stack, pipeline, data.get('client'), get_api_llm_config(), logger)
            query_build_time = time_since(query_build_start)

            # Compound Extraction
            logger.info("Compound Classification...")
            compound_classifier = CompoundClassifier(query_value, chains['compound'], logger)
            classified_compounds, classifier_response, reason = compound_classifier.explode_query()
            if not classified_compounds or 'queries' not in classified_compounds or not classified_compounds['queries']:
                logger.info("Compound Classification Failed...")
                response.update({
                    'compound_query_classification_response': classifier_response,
                    'compound_query_classification_success': False,
                    'compound_query_classification_reason': reason
                })
                queries_to_infer = {
                    '1': query_value
                }
            else:
                logger.info("Compound Classification Succeeded...")
                response.update({
                    'compound_query_classification_response': classifier_response,
                    'compound_query_classification': classified_compounds,
                    'compound_query_classification_success': True
                })
                queries_to_infer = classified_compounds['queries']

            response.update({
                'queries_to_infer': queries_to_infer
            })

            for query_value in queries_to_infer.values():
                constructed_query = construct_given_that_query(llm_inferences, query_value)

                # Query LLM
                logger.info("Querying LLM...")
                llm_query_start = cur_timestamp()
                llm_response = llm_query.query(constructed_query, chains['chain-context-only'])
                response.update(llm_response)
                llm_query_time = time_since(llm_query_start)

                # Response Validity
                logger.info("Determining if response answers question...")
                response_value = response['response']
                reason_query_start = cur_timestamp()
                verifier = ResponseVerifier(constructed_query, response_value, chains['chain-verify-response'], logger)
                is_answer, reason, answer_data = verifier.response_answers_question()
                reason_query_time = time_since(reason_query_start)
                llm_inferences.append(
                    {
                        'query': query_value,
                        'constructed_query': constructed_query,
                        'response': response_value,
                        'is_answer': is_answer,
                        'not_answer_reason': None if is_answer else reason,
                        'answer_data': answer_data,
                        'chunks_used': response['metadata']['contextbuilder']['chunks_used']
                    }
                )

        summarizer_start = cur_timestamp()
        response_summarizer = CompoundResponseSummarizer(chains['summarizer'], logger)
        final_response, response_was_summarized, has_valid_answers = response_summarizer.summarize(llm_inferences)
        summarizer_query_time = time_since(summarizer_start)
        response['source_urls'] = []

        if has_valid_answers:
            sources_start = cur_timestamp()
            chunks_used = []
            for inference in llm_inferences:
                chunks_used.extend(inference['chunks_used'])
            response_sources = ResponseSourceExtractor(chains['sources'], logger)
            sources_found, sources_reason, source_urls = response_sources.get_sources(query_value, final_response, chunks_used)
            response['sources_found'] = sources_found
            response['sources_reason'] = sources_reason
            response['source_urls'] = source_urls['source_urls']

        response.update({
            'query': data.get('query'),
            'response': final_response,
            'is_answer': has_valid_answers,
            'inference_results': list_of_dicts_to_dict(llm_inferences)
        })

        times = {
            'model_load_time': llm_model_load_time,
            'chain_build_time': chain_build_time,
            'query_lock_type': query_lock_type,
            'query_lock_wait_time': query_lock_wait_time,
            'rag_stack_build_time': rag_stack_build_time,
            'query_build_time': query_build_time,
            'malicious_query_classification_time': malicious_query_classification_time,
            'inference_time': llm_query_time,
            'reason_query_time': reason_query_time,
            'summary_time': summarizer_query_time,
            'response_was_summarized': response_was_summarized
        }

    response = calculate_response_times(response, g.start, times)
    response = process_response(response, pipeline, logger)
    error_response = handle_error(response, logger)
    if error_response:
        return error_response

    write_response_data(response)
    return Response(json_dumper(response, pretty=False), status=200, mimetype='application/json')


@app.route("/search", methods=['POST'])
def db_search_query():
    """Search RAG embeddings. Not logged or for general use."""
    global stacks, llm, chains

    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')

    logger.info("Embedding Search Recieved: query='%s...", query_value)

    query_lock_type = get_query_lock_type()
    logger.info(f"Waiting for {query_lock_type} lock...")
    query_lock_start = cur_timestamp()
    with get_query_lock():
        query_lock_wait_time = time_since(query_lock_start)
        logger.info(f"{query_lock_type} lock acquired after {query_lock_wait_time} seconds.")

        if not gpu_exclusive:
            logger.info("Building Query Stacks...")
            rag_stack_build_start = cur_timestamp()
            stacks = build_rag_stacks(logger)
            stack = stacks[pipeline]
            rag_stack_build_time = time_since(rag_stack_build_start)

        search_start = cur_timestamp()
        response = stack.search(query_value).to_dict()
        search_time = time_since(search_start)

    if 'error' in response:
        logger.error("Error summarizing document:")
        logger.error(response['error'])
        return Response(json_dumper(response, pretty=False), status=500, mimetype='application/json')    

    response['time'] = {}
    response['time']['query_lock_wait_time'] = query_lock_wait_time
    response['time']['rag_stack_build_time'] = rag_stack_build_time
    response['time']['search_time'] = search_time

    write_response_data(response)
    return Response(json_dumper(response, pretty=False), status=200, mimetype='application/json')

# API Start-up.
def start() -> None:
    """Starts the API server."""
    global stacks, llm, chains
    report_memory_use(logger)
    logger.info("Starting API server...")

    if gpu_exclusive:
        logger.info("Acquiring GPU lock...")
        gpu_lock.acquire()
        logger.info("GPU lock acquired.")
        signal.signal(signal.SIGINT, release_gpu_lock_and_exit)

        logger.info("Building Query Stacks...")
        stacks = build_rag_stacks(logger)

        logger.info("Loading LLM Model...")
        llm = LLM(logger, get_api_llm_config()).get()

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

def write_response_data(data: dict) -> None:
    """Writes the response data to a file."""
    data_dir = get_data_dir()
    summary_response_dir = f"{data_dir}/deckard_responses"
    makedirs(summary_response_dir, exist_ok=True)
    final_filepath = f"{summary_response_dir}/response_{cur_timestamp()}.json"
    with open(final_filepath, 'w') as f:
        f.write(json_dumper(data, pretty=True))

def calculate_response_times(response, start_time, times):
    response['time'] = times
    response['time']['total'] = time_since(start_time)
    return response

def process_response(response, pipeline, logger):
    postprocess_start_time = cur_timestamp()
    if response['is_answer']:
        config = get_rag_pipeline(pipeline)['rag']
        response_processor = load_class(config['response_processor']['module_name'], config['response_processor']['class_name'], [response['response'], logger])
        response['response'] = response_processor.get_processed_response()
    response['time']['postprocess_time'] = time_since(postprocess_start_time)
    return response

def handle_error(response, logger):
    if 'error' in response:
        logger.error("Error in LLM query:")
        logger.error(response['error'])
        response['is_answer'] = False
        return Response(json_dumper(response, pretty=False), status=500, mimetype='application/json')
    return None

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
