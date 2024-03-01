import requests
import sys

from deckard.core import get_logger
from deckard.interfaces.api import check_api_server_exit
from deckard.interfaces.api import get_api_uri
from logging import Logger

CMD_STRING = 'query:llm'

def query(args: list=sys.argv) -> None:
    log = get_logger()
    check_api_server_exit(log)
    validate_args(args, log)

    try:
        context = args[2]
    except:
        context = ""

    uri = get_api_uri('/query/raw')
    log.info(f"Querying {uri}...")
    r = requests.post(
        uri,
        json={
            "context": context,
            "query": args[1],
        }
    )
    print(r.text)

def validate_args(args: list, log: Logger) -> None:
    if len(args) < 1:
        print_usage(log)
        sys.exit(1)

    try:
        if args[1] == "":
            raise ValueError
    except:
        log.warning("Query cannot be empty")
        print_usage(log)
        sys.exit(1)

def print_usage(log: Logger) -> None:
    log.warning(f"Usage: poetry run {CMD_STRING} <query> <context>")
