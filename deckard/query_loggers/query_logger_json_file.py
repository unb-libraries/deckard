"""Provides the QueryLoggerJsonFile class."""
import os

from deckard.core import get_data_dir
from deckard.core import json_dumper
from deckard.core.time import cur_timestamp
from deckard.core.utils import open_file_write
from .query_logger import QueryLogger

class QueryLoggerJsonFile(QueryLogger):
    """Writes the basic query log to a JSON file.

    Args:
        query_id (str): The ID of the query.
        client (str): The client making the query.
        query (str): The query.
        response (str): The raw response.
        cleaned_response (str): The cleaned response.
        pipeline (str): The pipeline used to answer the query.
        circuit_breaker (bool): The circuit breaker flag.
        metadata (dict): The metadata for the query.
        start_time (float): The start time of the query.
        lock_wait (float): The lock wait time.
        failure (bool): The failure flag.

    Attributes:
        log (dict): The log entry.
        QUERY_LOG_DATA_PATH (str): The path to the query log data.
    """
    QUERY_LOG_DATA_PATH = os.path.join(
        get_data_dir(),
        'logs',
        'queries'
    )

    def write(self, query_id: str):
        """Writes the query log to a file.

        Args:
            query_id (str): The ID of the query.
        """
        with open_file_write(self._get_log_file_path(query_id)) as f:
            f.write(
                json_dumper(
                    self.log
                )
            )

    def _get_log_file_path(self, item_hash: str) -> str:
        """Returns the log file path.

        Args:
            item_hash (str): The hash of the item.

        Returns:
            str: The log file path.
        """
        if not os.path.exists(self.QUERY_LOG_DATA_PATH):
            os.makedirs(self.QUERY_LOG_DATA_PATH)
        timestamp = cur_timestamp()
        return os.path.join(
            self.QUERY_LOG_DATA_PATH,
            str(timestamp) + "_" + item_hash + ".json"
        )
