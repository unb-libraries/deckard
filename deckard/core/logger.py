import logging

from logging import Logger

def get_logger() -> Logger:
    """Gets the logger for the application.

    Returns:
        Logger: The logger for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s::%(module)s::%(levelname)s::%(message)s',
        datefmt='%d-%b-%y %H:%M:%S'
    )
    logger = logging.getLogger('deckard')
    return logger

def list_to_dict(l: list) -> dict:
    """Converts a list to a dictionary.

    This only exists because newrelic doesn't support lists in logs.

    Args:
        l (list): The list to convert.

    Returns:
        dict: The dictionary.
    """
    return {k: v for k, v in l}
