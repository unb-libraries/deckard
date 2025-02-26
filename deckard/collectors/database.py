import hashlib
import os
import time
from logging import Logger

from deckard.core import json_dumper, get_data_dir
from deckard.core.utils import open_file_write

class DatabaseCollector:
    """Collects data from a generic database. This is a base class.
    """

    SOURCE_SLUG = 'generic-database'

    def __init__(self, config: dict, log: Logger) -> None:
        self.log = log
        self.item_queue = []
        self.item_queue_index = 0

        self.cache_path = os.path.join(
            get_data_dir(),
            'collectors',
            self.SOURCE_SLUG,
            'cache'
        )

    def __iter__(self):
        return self

    def __next__(self):
        if self.item_queue_index < len(self.item_queue):
            self.item_queue_index += 1
            return self._process_item(
                self.item_queue[self.item_queue_index - 1]
            )
        raise StopIteration

    def name(self) -> str:
        return 'Generic Database Collector'

    def len(self) -> int:
        return len(self.item_queue)

    def _write_cache_file(self, content: str, hash_string: str) -> None:
        file_md5 = hashlib.md5(hash_string.encode("utf-8")).hexdigest()
        cache_file = os.path.join(
            self.cache_path,
            f'{file_md5}.txt'
        )
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        f = open_file_write(cache_file)
        f.write(content)

    def _process_item(self, item: dict) -> str:
        return item

    def _generate_metadata(self, source: str) -> str:
        return json_dumper(
            {
                "collector": self.name(),
                "source_type": self.SOURCE_SLUG,
                "timestamp": time.time(),
                "source": source
            }
        )

    def ignore_item(self, content: str) -> bool:
        return False
