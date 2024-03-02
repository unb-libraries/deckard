"""Provides a command to query the LLM directly, bypassing RAG pipelines."""
import sys
from logging import Logger

from deckard.core import get_logger
from deckard.interfaces.api import check_api_server_exit, post_query_to_api

DECKARD_CMD_STRING = 'query:llm'

def query(args: list=sys.argv) -> None:
    """Queries the LLM directly, bypassing RAG pipelines.

    Args:
        args (list, optional): The arguments for the query. Defaults to sys.argv.
    """
    log = get_logger()
    check_api_server_exit(log)
    validate_args(args, log)

    try:
        context = args[2]
    except Exception:
        context = ""

    r = post_query_to_api(
        args[1],
        '/query/raw',
        'deckard.query:llm',
        log,
        context=context,
    )
    print(r.text)

def validate_args(args: list, log: Logger) -> None:
    """Validates the arguments for the command and exits if invalid.

    Args:
        args (list): The arguments to validate.
        log (Logger): The logger to use.
    """
    if len(args) < 1:
        log_usage(log)
        sys.exit(1)

    try:
        if args[1] == "":
            raise ValueError
    except Exception:
        log.warning("Query cannot be empty")
        log_usage(log)
        sys.exit(1)

def log_usage(log: Logger) -> None:
    """Outputs the usage for the command.

    Args:
        log (Logger): The logger to use.
    """
    log.warning("Usage: poetry run %s <query> <context>", DECKARD_CMD_STRING)
