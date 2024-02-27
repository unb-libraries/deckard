from core.time import cur_timestamp
from core.time import time_since

class QueryLogger:
    def __init__(self, id, client, query, response, cleaned_response, endpoint, circuit_breaker, metadata, start_time, lock_wait, failure):
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
