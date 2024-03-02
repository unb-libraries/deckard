"""Provides a command to build RAG pipelines."""
import sys
from logging import Logger

from deckard.core import get_rag_pipelines, get_rag_pipeline, get_logger, available_rag_pipelines_message
from deckard.rag import RagBuilder

DECKARD_CMD_STRING = 'build:rag'

def start(args: list=sys.argv) -> None:
    """Starts the RAG pipeline builder.

    Args:
        args (list, optional): The arguments for the builder. Defaults to sys.argv.
    """
    log = get_logger()
    validate_args(args, log)
    pipeline = get_rag_pipeline(args[1])
    log.info("Building Pipeline %s", pipeline['name'])
    builder = RagBuilder(pipeline['rag'], log)
    builder.build()

def validate_args(args: list, log: Logger) -> None:
    """Validates the arguments for the command and exits if invalid.

    Args:
        args (list): The arguments to validate.
        log (Logger): The logger to use.
    """
    pipelines = get_rag_pipelines()
    if len(args) < 2:
        log.warning("Usage: poetry run %s <pipeline>", DECKARD_CMD_STRING)
        log.info(available_rag_pipelines_message())
        sys.exit(1)

    if args[1] not in pipelines:
        log.error("Pipeline %s not found", args[1])
        log.info(available_rag_pipelines_message())
        sys.exit(1)
