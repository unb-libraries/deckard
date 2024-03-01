import json
import os

from deckard.core import get_data_dir
from deckard.core import json_dumper
from deckard.core.time import cur_timestamp

from .query_logger import QueryLogger

class QueryLoggerJsonFile(QueryLogger):
    QUERY_LOG_DATA_PATH = os.path.join(
        get_data_dir(),
        'logs',
        'queries'
    )

    def write(self, id: str):
        with open(self.getLogfilePath(id), 'w') as f:
            f.write(
                json_dumper(
                    self.log
                )
            )

    def getLogfilePath(self, item_hash: str) -> str:
        if not os.path.exists(self.QUERY_LOG_DATA_PATH):
            os.makedirs(self.log_path)
        timestamp = cur_timestamp()
        return os.path.join(
            self.QUERY_LOG_DATA_PATH,
            str(timestamp) + "_" + item_hash + ".json"
        )
