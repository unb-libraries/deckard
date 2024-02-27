import requests
import sys

from core.logger import get_logger
from interfaces.api import check_api_server_exit
from interfaces.api import get_api_uri

CMD_STRING = 'query:llm'

def query(args=sys.argv):
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

def validate_args(args, log):
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

def print_usage(log):
    log.warning(f"Usage: poetry run {CMD_STRING} <query> <context>")
