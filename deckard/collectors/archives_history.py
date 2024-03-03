"""Provides the DatabaseCollector class."""
import time
from logging import Logger

from deckard.core import json_dumper
from .mysql import MySQLCollector

class ArchivesHistoryCollector(MySQLCollector):
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

    def _generate_metadata(self, url: str) -> str:
        return json_dumper(
            {
                "collector": self.name(),
                "source_type": "webpage",
                "timestamp": time.time(),
                "source": url
            }
        )

    def ignore_item(self) -> bool:
        return False
