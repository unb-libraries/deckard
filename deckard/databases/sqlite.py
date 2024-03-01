import os
import sqlite3
import sys

from deckard.core import get_data_dir

from .context_database import ContextDatabase

class SQLite(ContextDatabase):
    CONTEXT_TABLE_NAME = "llm_document_chunks"
    DATA_PATH = os.path.join(
        get_data_dir(),
        'databases',
        'sqlite'
    )

    def __init__(self, name, log, create_if_not_exists=False):
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
        self.conn = None

        try:
            self.conn = sqlite3.connect(db_filepath, check_same_thread=False)
        except:
            log.error(f"Failed to connect to database: {name}")

    def flushData(self):
        self.conn.execute(f"DROP TABLE IF EXISTS {self.CONTEXT_TABLE_NAME}")

    def createTable(self):
        data = "doc_id TEXT, chunk_id INT, text TEXT"
        self.conn.execute(f"CREATE TABLE {self.CONTEXT_TABLE_NAME} ({data})")

    def addContexts(self, document, create_table=False):
        if create_table:
            self.createTable()
        rows = []
        for idx, chunk in enumerate(document['raw_chunks']):
            rows.append([
                document['id'],
                idx,
                chunk
            ])
        self.log.info(f"Adding document {document['id']} context pieces to SQLite.")
        self.conn.executemany(f"INSERT INTO {self.CONTEXT_TABLE_NAME} VALUES (?,?,?)", rows)
        self.conn.commit()

