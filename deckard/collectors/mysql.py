"""Provides the DatabaseCollector class."""
from logging import Logger

from deckard.core import json_dumper
from .database import DatabaseCollector

class MySQLCollector(DatabaseCollector):
    SOURCE_SLUG = 'generic-mysql-database'
    ITEM_QUERY_SQL = ''

    def __init__(self, config: dict, log: Logger) -> None:
        super().__init__(config, log)

    def name(self) -> str:
        return 'Mysql Database Collector'

    def len(self) -> int:
        return len(self.item_queue)

    def ignore_item(self, content: str) -> bool:
        return False
