"""Provides the QueryLogger class."""
from deckard.core.time import cur_timestamp
from deckard.core.time import time_since

class QueryLogger:
    """Builds the log for a query and its responses.

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
    """
    def __init__(
        self,
        query_id: str,
        client: str,
        query: str,
        response: str,
        cleaned_response: str,
        pipeline: str,
        circuit_breaker: bool,
        metadata: dict,
        start_time: float,
        lock_wait: float,
        failure: bool
    ) -> None:
        self.log = {
                "id": query_id,
                "client": client,
                "pipeline": pipeline,
                "timestamp": cur_timestamp(),
                "query": query,
                "raw_response": response,
                "query_time": time_since(start_time) - lock_wait,
                "lock_wait": lock_wait,
                "response": cleaned_response,
                "circuit_breaker": circuit_breaker,
                "failure": failure,
                "metadata": metadata
        }
