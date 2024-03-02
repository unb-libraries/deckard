"""Provides a command to search for embeddings within RAG databases."""
import logging
import sys
from logging import Logger

from deckard.core import available_rag_pipelines_message, get_logger, get_rag_pipeline
from deckard.interfaces.api import check_api_server_exit, post_query_to_api

DECKARD_CMD_STRING = 'search:embeddings'

def search(args: list=sys.argv) -> None:
    """Searches for embeddings within RAG databases.

    Args:
        args (list, optional): The arguments for the search. Defaults to sys.argv.
    """
    log = get_logger()
    validate_args(args, log)
    check_api_server_exit(log)

    r = post_query_to_api(
        args[2],
        '/search',
        'deckard.%s',DECKARD_CMD_STRING,
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
    logging.info("Pipeline: %s", args[1])
    pipeline = get_rag_pipeline(args[1])

    if pipeline is None:
        log.warning("Pipeline %s not found", args[1])
        log_usage(log)
        log.info(available_rag_pipelines_message())
        sys.exit(1)

    try:
        if args[2] == "":
            raise ValueError
    except Exception:
        log.warning("Search term cannot be empty")
        log_usage(log)
        sys.exit(1)

def log_usage(log: Logger) -> None:
    """Outputs the usage message for the command.

    Args:
        log (Logger): The logger to use.
    """
    log.warning("Usage: poetry run %s <pipeline> <search>", DECKARD_CMD_STRING)
