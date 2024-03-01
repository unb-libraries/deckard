import json
import socket
import sys

from core.builders import build_llm_chains
from core.builders import build_rag_stacks
from core.config import get_api_host
from core.config import get_api_llm_config
from core.config import get_api_port
from core.LLM import LLM
from core.LLMQuery import LLMQuery
from core.logger import get_logger
from core.time import cur_timestamp
from core.time import time_since
from core.utils import report_memory_use
from flask import current_app
from flask import Flask
from flask import g
from flask import request
from logging import Logger
from threading import Lock

CMD_STRING = 'api:start'

app = Flask(__name__)

# Lock to prevent concurrent use of the GPU.
# Although the model is only loaded into the GPU once, we should investigate
# in this POC what would happen if multiple threads tried to use the GPU
# simultaneously.
gpu_lock = Lock()

@app.before_request
def before_request():
    g.start = cur_timestamp()

# Cheery default.
@app.route("/")
def hello():
    return "Endpoint Disabled."

# Raw LLM query endpoint. Invoke chain directly. Not intended for general use.
@app.route("/query/raw", methods=['POST'])
def rawquery():
    log = get_logger()
    data = request.json
    chain = current_app.config['chains']['chain-context-plus']
    with gpu_lock:
        chain_reponse = chain.invoke(
            {
                "context": data.get('context'),
                "query": data.get('query')
            }
        )
        return {
            "response": chain_reponse['text']
        }


# RAG query endpoint.
@app.route("/query", methods=['POST'])
def libpages_query():
    data = request.json
    query_value = data.get('query')
    endpoint_value = data.get('endpoint')

    # @TODO: Error handling for missing endpoint.

    stack = current_app.config['rag_stacks'][endpoint_value]

    query = LLMQuery(
        stack,
        endpoint_value,
        data.get('client'),
        get_api_llm_config()
    )
    now = cur_timestamp()
    with gpu_lock:
        return query.query(
            query_value,
            current_app.config['chains']['chain-context-only'],
            g.start,
            time_since(now),
            True
        )

# RAG embedding search endpoint. Not intended for general use.
@app.route("/search", methods=['POST'])
def db_search_query():
    data = request.json
    query_value = data.get('query')
    endpoint_value = data.get('endpoint')
    # @TODO: Error handling for missing endpoint.
    stack = current_app.config['rag_stacks'][endpoint_value]

    with gpu_lock:
        return result_wrapper(
            stack.search(query_value).to_dict()
        )

# API Start-up.
def start() -> None:
    log = get_logger()

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
    if not api_server_up():
        log.error("API server not running")
        sys.exit(1)

def api_server_up() -> bool:
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = (get_api_host(), get_api_port())
    return a_socket.connect_ex(location) == 0

def get_api_uri(endpoint: str='/query/raw') -> str:
    return 'http://' + get_api_host() + ':' + str(get_api_port()) + endpoint

def result_wrapper(results: dict) -> str:
    return json.dumps(
        results,
        indent=2
    )
