import logging
import requests
import sys

from interfaces.api import get_api_uri, check_api_server_exit
from core.config import get_workflow
from core.config import get_workflow_encoder
from core.config import get_workflows
from core.logger import get_logger
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
        print_get_workflows(log)
        sys.exit(1)

    logging.info(f"Endpoint: {args[1]}")
    workflow = get_workflow(args[1])

    if workflow is None:
        log.warning(f"Endpoint {args[1]} not found")
        print_usage(log)
        print_get_workflows(log)
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

def print_get_workflows(log: Logger) -> None:
    workflows = get_workflows()
    log.warning("Available workflows:")
    for workflow in workflows:
        log.warning(f"* {workflow}")
