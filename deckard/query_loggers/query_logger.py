from deckard.core.time import cur_timestamp
from deckard.core.time import time_since

class QueryLogger:
    def __init__(
        self,
        id: str,
        client: str,
        query: str,
        response: str,
        cleaned_response: str,
        endpoint: str,
        circuit_breaker: bool,
        metadata: dict,
        start_time: float,
        lock_wait: float,
        failure: bool
    ) -> None:
        self.log = {
                "id": id,
                "client": client,
                "endpoint": endpoint,
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
