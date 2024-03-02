"""Provides a command to query RAG pipelines."""
import sys
from logging import Logger

from deckard.core import get_logger
from deckard.core import get_rag_pipelines
from deckard.interfaces.api import check_api_server_exit, post_query_to_api

DECKARD_CMD_STRING = 'query:rag'

def query(args: list=sys.argv):
    """Queries RAG pipelines.

    Args:
        args (list, optional): The arguments for the query. Defaults to sys.argv.
    """
    log = get_logger()
    validate_args(args, log)
    check_api_server_exit(log)

    r = post_query_to_api(
        args[2],
        '/query',
        'deckard.query:rag',
        log,
        pipeline=args[1]
    )
    print(r.text)

def validate_args(args: list, log: Logger) -> None:
    """Validates the arguments for the command and exits if invalid.

    Args:
        args (list): The arguments to validate.
        log (Logger): The logger to use.
    """
    if len(args) < 2:
        log_usage(log)
        sys.exit(1)
    pipeline = get_rag_pipelines()
    if args[1] not in pipeline:
        log.warning("pipeline %s not found", args[1])
        log_usage(log)
        sys.exit(1)
    try:
        if args[2] == "":
            raise ValueError
    except Exception:
        log.warning("Query cannot be empty")
        log_usage(log)
        sys.exit(1)

def log_usage(log: Logger) -> None:
    """Logs the usage for the command.

    Args:
        log (Logger): The logger to use.
    """
    log.warning("Usage: poetry run %s <pipelineid> <query>", DECKARD_CMD_STRING)
