import json
import os

from core.config import get_data_dir
from core.QueryLogger import QueryLogger
from core.time import cur_timestamp

class QueryLoggerJsonFile(QueryLogger):
    QUERY_LOG_DATA_PATH = os.path.join(
        get_data_dir(),
        'logs',
        'queries'
    )

    def write(self, id: str):
        with open(self.getLogfilePath(id), 'w') as f:
            f.write(
                json.dumps(
                    self.log,
                    indent=2
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
