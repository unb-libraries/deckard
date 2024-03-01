import sys

from deckard.core import get_rag_pipelines, get_rag_pipeline, get_logger
from deckard.rag import RagBuilder

from logging import Logger

CMD_STRING = 'build:rag'

def start(args: list=sys.argv) -> None:
    log = get_logger()
    validate_args(args, log)
    pipeline = get_rag_pipeline(args[1])
    log.info(f"Building Endpoint {pipeline['name']}")
    builder = RagBuilder(pipeline['rag'], log)
    builder.build()

def validate_args(args: list, log: Logger) -> None:
    pipelines = get_rag_pipelines()
    if len(args) < 2:
        log.warning(f"Usage: poetry run {CMD_STRING} <pipeline>")
        print_get_rag_pipelines(log, pipelines)
        sys.exit(1)

    if args[1] not in pipelines:
        log.error(f"Endpoint {args[1]} not found")
        print_get_rag_pipelines(log, pipelines)
        sys.exit(1)

def print_get_rag_pipelines(log: Logger, pipelines: dict) -> None:
    log.warning("Available RAG pipelines:")
    for pipeline in pipelines:
        log.warning(f"  {pipeline}")
