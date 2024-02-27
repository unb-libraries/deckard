import os
import sqlite3
import sys

from core.config import get_data_dir

class SQLite:
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

    # @TODO: Move this to a new contextbuilder.
    def buildContext(self, vec_results, context_size):
        context = ""
        for ind in vec_results.index:
            sql = f"SELECT text, chunk_id FROM {self.CONTEXT_TABLE_NAME} WHERE doc_id = '{vec_results['doc_id'][ind]}' ORDER BY chunk_id ASC"
            cursor = self.conn.execute(sql)
            doc_chunks = cursor.fetchall()
            document = ""

            # @NOTE: This method does not work well with chunk overlap.
            # Reassemble the original document.
            for doc_chunk in doc_chunks:
                doc_len = len(document)
                if doc_chunk[1] == vec_results['chunk_id'][ind]:
                    middle_point = doc_len + len(doc_chunk[0]) / 2
                document = document + doc_chunk[0] + "\n"

            # Add the document to the context.
            if len(document) + len(context) <= context_size:
                context = context + document + "\n"
            else:
                # The whole document is too much to add to context. Find out how much we can add.
                context_left = context_size - len(context)
                # Extract this amount from the document with the middle point as the center.
                start = middle_point - context_left / 2
                end = middle_point + context_left / 2
                context = context + document[int(start):int(end)] + "\n"
                # We've exhausted the context.
                return context
        return context

