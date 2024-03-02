"""Provides the core API server for Deckard."""
import socket
import sys
from logging import Logger
from threading import Lock

import requests
from flask import current_app
from flask import Flask
from flask import g
from flask import request

from deckard.core import get_logger, json_dumper
from deckard.core.builders import build_llm_chains, build_rag_stacks
from deckard.core.config import get_api_host, get_api_llm_config, get_api_port
from deckard.core.defaults import default_http_request_timeout
from deckard.core.time import cur_timestamp, time_since
from deckard.core.utils import report_memory_use
from deckard.llm import LLM, LLMQuery

DECKARD_CMD_STRING = 'api:start'

app = Flask(__name__)

""" Lock to prevent concurrent use of the GPU. Although the model is only loaded
into the GPU once, we should investigate in this POC what would happen if
multiple threads tried to use the GPU simultaneously."""
gpu_lock = Lock()
log = get_logger()

@app.before_request
def before_request():
    """Set the start time for the request."""
    g.start = cur_timestamp()

# Cheery default.
@app.route("/")
def hello():
    """Default endpoint."""
    return "Endpoint Disabled."

@app.route("/query/raw", methods=['POST'])
def rawquery():
    """Raw LLM query endpoint. Invoke chain directly. Not intended for general use."""
    data = request.json
    chain = current_app.config['chains']['chain-context-plus']
    context = data.get('context'),
    query = data.get('query')
    log.info("Raw LLM Query Recieved with context %s and query %s...", context, query)
    log.info("Waiting for GPU lock...")
    with gpu_lock:
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
@app.route("/query", methods=['POST'])
def libpages_query():
    """RAG query endpoint."""
    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')

    # @TODO: Error handling for incorrect pipeline.

    stack = current_app.config['rag_stacks'][pipeline]

    query = LLMQuery(
        stack,
        pipeline,
        data.get('client'),
        get_api_llm_config(),
        log
    )
    now = cur_timestamp()
    log.info("Query %s waiting on gpu_lock", query.query_id)
    with gpu_lock:
        return query.query(
            query_value,
            current_app.config['chains']['chain-context-only'],
            g.start,
            time_since(now),
            True
        )

@app.route("/search", methods=['POST'])
def db_search_query():
    """RAG search endpoint. Not intended for general use."""
    data = request.json
    query_value = data.get('query')
    pipeline = data.get('pipeline')
    # @TODO: Error handling for missing endpoint.
    stack = current_app.config['rag_stacks'][pipeline]
    log.info("Embedding Search Recieved with query %s...", query_value)
    log.info("Waiting for GPU lock...")
    with gpu_lock:
        return json_dumper(
            stack.search(query_value).to_dict()
        )

# API Start-up.
def start() -> None:
    """Starts the API server."""
    log.info("Loading LLM...")
    llm = LLM(log, get_api_llm_config()).get()
    app.config['llm'] = llm

    log.info("Building LLM Chains...")
    app.config['chains'] = build_llm_chains(llm)

    log.info("Building Query Stacks...")
    app.config['rag_stacks'] = build_rag_stacks(log)

    report_memory_use(log)
    log.info("Starting API server...")
    app.run(port=get_api_port())

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

def get_api_uri(endpoint: str='/query/raw') -> str:
    """Gets the URI for the API server.

    Args:
        endpoint (str, optional): The endpoint to use. Defaults to '/query/raw'.

    Returns:
        str: The URI for the API server.
    """
    return 'http://' + get_api_host() + ':' + str(get_api_port()) + endpoint

def post_query_to_api(
        query: str,
        endpoint: str,
        client: str,
        log: Logger,
        context: str='',
        pipeline: str=''
    ) -> requests.Response:
    """Posts a query to the API server.

    Args:
        query (str): The query to post.
        endpoint (str): The endpoint to query.
        client (str): The client name to assert.
        log (Logger): The logger to use.
        context (str, optional): The context to use. Defaults to ''.
        pipeline (str, optional): The RAG pipeline to use. Defaults to ''.

    Returns:
        requests.Response: The response from the API server.
    """
    uri = get_api_uri(endpoint)
    log.info("Querying %s...", uri)
    return requests.post(
        uri,
        json={
            "context": context,
            "client": client,
            "pipeline": pipeline,
            "query": query
        },
        timeout=default_http_request_timeout()
    )
