import sys

from core.config import get_workflows
from core.config import get_workflow
from core.logger import get_logger
from core.RagBuilder import RagBuilder

CMD_STRING = 'build:rag'

def start(args=sys.argv):
    log = get_logger()
    validate_args(args, log)
    workflow = get_workflow(args[1])
    log.info(f"Building Endpoint {workflow['name']}")
    builder = RagBuilder(workflow['rag'], log)
    builder.build()

def validate_args(args, log):
    workflows = get_workflows()
    if len(args) < 2:
        log.warning(f"Usage: poetry run {CMD_STRING} <workflow>")
        print_get_workflows(log, workflows)
        sys.exit(1)

    if args[1] not in workflows:
        log.error(f"Endpoint {args[1]} not found")
        print_get_workflows(log, workflows)
        sys.exit(1)

def print_get_workflows(log, workflows):
    log.warning("Available endpoints:")
    for workflow in workflows:
        log.warning(f"  {workflow}")
