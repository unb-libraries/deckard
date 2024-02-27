import requests
import sys

from core.config import get_workflows
from core.logger import get_logger
from interfaces.api import check_api_server_exit
from interfaces.api import get_api_uri

CMD_STRING = 'query:rag'

def query(args=sys.argv):
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

def validate_args(args, log):
    if len(args) < 2:
        print_usage(log)
        sys.exit(1)
    workflow = get_workflows()
    if args[1] not in workflow:
        log.warning(f"Workflow {args[1]} not found")
        print_usage(log)
        sys.exit(1)
    try:
        if args[2] == "":
            raise ValueError
    except:
        log.warning("Query cannot be empty")
        print_usage(log)
        sys.exit(1)

def print_usage(log):
    log.warning(f"Usage: poetry run {CMD_STRING} <workflowid> <query>")
