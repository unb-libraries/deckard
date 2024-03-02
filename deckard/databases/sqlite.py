import os
import sqlite3
import sys
from logging import Logger

from deckard.core import get_data_dir
from .context_database import ContextDatabase

class SQLite(ContextDatabase):
    """Provides a SQLite interface for adding and querying embeddings.

    Args:
        name (str): The name of the database.
        log (Logger): The logger for the database.
        create_if_not_exists (bool): Whether to create the database if it does not exist.

    Attributes:
        CONTEXT_TABLE_NAME (str): The name of the table for the context.
        DATA_PATH (str): The path to the data directory.
        log (Logger): The logger for the database.
        connection (sqlite3.Connection): The connection to the database.
    """

    CONTEXT_TABLE_NAME = "llm_document_chunks"
    DATA_PATH = os.path.join(
        get_data_dir(),
        'databases',
        'sqlite'
    )

    def __init__(self,
            name: str,
            log: Logger,
            create_if_not_exists: bool=False
        ) -> None:
        self.log = log
        db_filepath = os.path.join(self.DATA_PATH, '.' + name)
        if not os.path.exists(self.DATA_PATH):
            if create_if_not_exists:
                self.log.info(f"Creating Database: {name}")
                os.makedirs(self.DATA_PATH)
            else:
                self.log.error("Database does not exist.")
                sys.exit(1)
        self.log.info(f"Connecting to Database: {name}")
        self.connection = None

        try:
            self.connection = sqlite3.connect(db_filepath, check_same_thread=False)
        except Exception:
            log.error("Failed to connect to database: %s", name)

    def flush_data(self):
        self.connection.execute(f"DROP TABLE IF EXISTS {self.CONTEXT_TABLE_NAME}")

    def _create_table(self):
        data = "doc_id TEXT, chunk_id INT, text TEXT"
        self.connection.execute(f"CREATE TABLE {self.CONTEXT_TABLE_NAME} ({data})")

    def add_contexts(self, document, create_table=False):
        if create_table:
            self._create_table()
        rows = []
        for idx, chunk in enumerate(document['raw_chunks']):
            rows.append([
                document['id'],
                idx,
                chunk
            ])
        self.log.info("Adding document %s context pieces to SQLite.", document['id'])
        self.connection.executemany(f"INSERT INTO {self.CONTEXT_TABLE_NAME} VALUES (?,?,?)", rows)
        self.connection.commit()

