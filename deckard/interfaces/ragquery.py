import requests
import sys

from logging import Logger

from deckard.core import get_rag_pipelines
from deckard.core import get_logger
from deckard.interfaces.api import check_api_server_exit
from deckard.interfaces.api import get_api_uri

CMD_STRING = 'query:rag'

def query(args: list=sys.argv):
    log = get_logger()
    validate_args(args, log)
    check_api_server_exit(log)

    uri = get_api_uri('/query')
    log.info(f"Querying {uri}...")
    r = requests.post(
        uri,
        json={
            "endpoint": args[1],
            "query": args[2],
            "client": 'ragquery',
        }
    )
    print(r.text)

def validate_args(args: list, log: Logger) -> None:
    if len(args) < 2:
        print_usage(log)
        sys.exit(1)
    pipeline = get_rag_pipelines()
    if args[1] not in pipeline:
        log.warning(f"pipeline {args[1]} not found")
        print_usage(log)
        sys.exit(1)
    try:
        if args[2] == "":
            raise ValueError
    except:
        log.warning("Query cannot be empty")
        print_usage(log)
        sys.exit(1)

def print_usage(log: Logger) -> None:
    log.warning(f"Usage: poetry run {CMD_STRING} <pipelineid> <query>")
