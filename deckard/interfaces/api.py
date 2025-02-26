"""Provides the core API server for Deckard."""
import socket
import sys

from logging import Logger
from filelock import FileLock
from flask import current_app, Flask, g, request, Response
from os import makedirs
from waitress import serve as waitress_serve

from deckard.core import get_logger, json_dumper
from deckard.core.builders import build_llm_chains, build_rag_stacks
from deckard.core.config import get_api_host, get_api_llm_config, get_api_port, get_data_dir, get_gpu_lockfile
from deckard.core.time import cur_timestamp, time_since
from deckard.core.utils import report_memory_use, gen_uuid
from deckard.llm import LLM, LLMQuery, ResponseVerifier, MaliciousClassifier, fail_response

DECKARD_CMD_STRING = 'api:start'

app = Flask(__name__)

gpu_lock = FileLock(get_gpu_lockfile())
logger = get_logger()

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
    data = request.json
    context = data.get('context')
    query = data.get('query')
    logger.info("Raw LLM Query Recieved with context %s and query %s...", context, query)
 
    logger.info("Waiting for GPU lock...")
    gpu_request_lock_start = cur_timestamp()
    with gpu_lock:
        gpu_lock_wait_time = time_since(gpu_request_lock_start)
        logger.info("GPU lock acquired after %s seconds.", gpu_lock_wait_time)
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
            "response": chain_reponse['text']
        }

# RAG query endpoint.
@app.route("/query/v1", methods=['POST'])
def libpages_query():
    """RAG query endpoint."""
    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')
    response = {}

    response['id'] = gen_uuid()
    response['query'] = query_value
    response['pipeline'] = pipeline

    logger.info("Waiting for GPU lock...")
    gpu_request_lock_start = cur_timestamp()
    with gpu_lock:
        gpu_lock_wait_time = time_since(gpu_request_lock_start)
        logger.info("GPU lock acquired after %s seconds.", gpu_lock_wait_time)

        logger.info("Building Query Stacks...")
        rag_stack_build_start = cur_timestamp()
        stacks = build_rag_stacks(logger)
        stack = stacks[pipeline]
        rag_stack_build_time = time_since(rag_stack_build_start)

        llm_model_load_start = cur_timestamp()
        llm = LLM(logger, get_api_llm_config()).get()
        llm_model_load_time = time_since(llm_model_load_start)

        logger.info("Building LLM Chains...")
        chain_build_start = cur_timestamp()
        chains = build_llm_chains(llm)
        chain_build_time = time_since(chain_build_start)

        logger.info("Classifying Offensiveness...")
        is_malicious_start = cur_timestamp()
        malicious_classifier = MaliciousClassifier(
            query_value,
            chains['malicious'],
            logger
        )
        classification, reason, classification_data = malicious_classifier.question_has_malicious_intent()
        malicious_query_classification_time = time_since(is_malicious_start)
        response['malicious_query_classification'] = classification
        response['malicious_query_classification_reason'] = reason
        response['malicious_query_classification_response'] = classification_data

        if classification != 'Safe':
            logger.info("Classification: Not Safe...")
            response['response'] = fail_response()
            response['is_answer'] = False
            if reason in classification_data:
                response['malicious_query_classification_reason'] = classification_data['reason']
            query_build_time = 0
            llm_query_time = 0
            reason_query_time = 0
            postprocess_time = 0
        else:
            logger.info("Classification: Safe...")
            logger.info("Querying LLM...")
            query_build_start = cur_timestamp()
            llm_query = LLMQuery(
                response['id'],
                stack,
                pipeline,
                data.get('client'),
                get_api_llm_config(),
                logger
            )
            query_build_time = time_since(query_build_start)

            llm_query_start = cur_timestamp()
            llm_response = llm_query.query(
                query_value,
                chains['chain-context-only'],
            )
            response.update(llm_response)
            llm_query_time = time_since(llm_query_start)

            # Verify if the response addresses the query.
            logger.info("Determining if response answers question...")
            response_value = response['response']
            reason_query_start = cur_timestamp()
            verifier = ResponseVerifier(
                query_value,
                response_value,
                chains['chain-verify-response'],
                logger
            )
            is_answer, reason, answer_data = verifier.response_answers_question()
            reason_query_time = time_since(reason_query_start)

            if not is_answer:
                logger.info("Response did NOT addresses query...")
                response['response'] = llm_query.FAIL_RESPONSE_MESSAGE
                response['is_answer'] = False
                response['not_answer_reason'] = reason
            else:
                logger.info("Response did addresses query...")
                response['is_answer'] = True
                response['not_answer_reason'] = None
            response['answer_data'] = answer_data

    postprocess_start_time = cur_timestamp()

    # Strip nonsense like "Based on the provided context,"
    obtuse_prefixes = [
        'Based on the provided context,'
    ]
    for prefix in obtuse_prefixes:
        response['response'] = response['response'].replace(prefix, '').strip()

    postprocess_time = time_since(postprocess_start_time)

    response['time'] = {}
    response['time']['model_load_time'] = llm_model_load_time
    response['time']['chain_build_time'] = chain_build_time
    response['time']['gpu_lock_wait_time'] = gpu_lock_wait_time
    response['time']['rag_stack_build_time'] = rag_stack_build_time
    response['time']['query_build_time'] = query_build_time
    response['time']['malicious_query_classification_time'] = malicious_query_classification_time

    response['time']['inference_time'] = llm_query_time
    response['time']['reason_query_time'] = reason_query_time
    response['time']['postprocess_time'] = postprocess_time

    response['time']['total'] = time_since(g.start)

    if 'error' in response:
        logger.error("Error in LLM query:")
        logger.error(response['error'])
        response['is_answer'] = False
        return Response(json_dumper(response, pretty=False), status=500, mimetype='application/json')    

    write_response_data(response)
    return Response(json_dumper(response, pretty=False), status=200, mimetype='application/json')

@app.route("/search", methods=['POST'])
def db_search_query():
    """Search RAG embeddings. Not logged or for general use."""
    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')

    logger.info("Embedding Search Recieved: query='%s...", query_value)

    logger.info("Waiting for GPU lock...")
    gpu_request_lock_start = cur_timestamp()
    with gpu_lock:
        gpu_lock_wait_time = time_since(gpu_request_lock_start)

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
    response['time']['gpu_lock_wait_time'] = gpu_lock_wait_time
    response['time']['rag_stack_build_time'] = rag_stack_build_time
    response['time']['search_time'] = search_time

    write_response_data(response)
    return Response(json_dumper(response, pretty=False), status=200, mimetype='application/json')

# API Start-up.
def start() -> None:
    """Starts the API server."""
    report_memory_use(logger)
    logger.info("Starting API server...")
    waitress_serve(app, host=get_api_host(), port=get_api_port())

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