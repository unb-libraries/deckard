import json
import time

from logging import Logger

class DatabaseCollector:
    ITEM_QUERY_SQL = ''

    def __init__(self, config: dict, log: Logger) -> None:
        self.log = log
        self.item_queue = []
        self.item_queue_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.item_queue_index < len(self.item_queue):
            return ''
        else:
            raise StopIteration

    def name(self) -> str:
        return 'Generic Database Collector'

    def len(self) -> int:
        return len(self.item_queue)

    def generate_metadata(self, url: str) -> str:
        return json.dumps(
            {
                "collector": self.name(),
                "source_type": "webpage",
                "timestamp": time.time(),
                "source": url
            }
        )

    def ignoreItem(self, page_content: str) -> bool:
        for ignore_string in self.IGNORE_PAGE_STRINGS:
            if ignore_string in page_content:
                return True
        return False
