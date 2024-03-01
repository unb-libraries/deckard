import logging
import requests
import sys

from deckard.interfaces.api import get_api_uri, check_api_server_exit
from deckard.core import get_rag_pipeline
from deckard.core import get_rag_pipelines
from deckard.core import get_logger
from logging import Logger

CMD_STRING = 'search:embeddings'

def search(args: list=sys.argv) -> None:
    log = get_logger()
    validate_args(args, log)
    check_api_server_exit(log)

    uri = get_api_uri('/search')
    log.info(f"Querying {uri}...")
    r = requests.post(
        uri,
        json={
            "endpoint": args[1],
            "query": args[2],
            "client": "poetry"
        }
    )
    print(r.text)

def validate_args(args: list, log: Logger) -> None:
    if len(args) < 2:
        print_usage(log)
        print_get_rag_pipelines(log)
        sys.exit(1)

    logging.info(f"Endpoint: {args[1]}")
    pipeline = get_rag_pipeline(args[1])

    if pipeline is None:
        log.warning(f"Endpoint {args[1]} not found")
        print_usage(log)
        print_get_rag_pipelines(log)
        sys.exit(1)

    try:
        if args[2] == "":
            raise ValueError
    except:
        log.warning("Search term cannot be empty")
        print_usage(log)
        sys.exit(1)

def print_usage(log: Logger) -> None:
    log.warning(f"Usage: poetry run {CMD_STRING} <endpoint> <search>")

def print_get_rag_pipelines(log: Logger) -> None:
    pipelines = get_rag_pipelines()
    log.warning("Available RAG pipelines:")
    for pipeline in pipelines:
        log.warning(f"* {pipeline}")
