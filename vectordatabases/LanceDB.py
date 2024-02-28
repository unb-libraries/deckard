import lancedb
import os
import pyarrow as pa
import sys

from core.config import get_data_dir
from lance.vector import vec_to_table

class LanceDB:
    EMBEDDINGS_TABLE_NAME = "llm_embeddings"
    DATA_PATH = os.path.join(
        get_data_dir(),
        'databases',
        'lancedb'
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
        self.connection = lancedb.connect(db_filepath)
        try:
            self.embeddings_table = self.connection.open_table(self.EMBEDDINGS_TABLE_NAME)
        except:
            self.log.warning(f"Table: {self.EMBEDDINGS_TABLE_NAME} does not exist.")

    def flushData(self):
        self.connection.drop_table(
            self.EMBEDDINGS_TABLE_NAME,
            ignore_missing=True
        )

    def createTable(self, data):
        self.embeddings_table = self.connection.create_table(
            self.EMBEDDINGS_TABLE_NAME,
            data=data,
            mode="overwrite"
        )

    def addEmbeddings(self, document, embedding_id_start, create_table=False):
        embedding_id = embedding_id_start

        ids = []
        doc_ids = []
        chunk_ids = []
        texts = []
        embeddings = []

        for idx, embedding in enumerate(document['embeddings']):
            embedding_id += 1
            ids.append(embedding_id)
            doc_ids.append(document['id'])
            chunk_ids.append(idx)
            texts.append(document['raw_chunks'][idx])
            embeddings.append(embedding)

        item_metadata = {
            'id': ids,
            'text': texts,
            'doc_id': doc_ids,
            'chunk_id': chunk_ids
        }
        textual_data = pa.Table.from_pydict(item_metadata)
        et = vec_to_table(embeddings)
        item = textual_data.append_column("vector", et["vector"])
        self.log.info(f"Adding document {document['id']} {len(ids)} embeddings to LanceDB.")
        if create_table:
            self.createTable(item)
        else:
            self.embeddings_table.add(item)
        return embedding_id

    def query(self, query, limit=25, max_distance=5):
        results = self.embeddings_table.search(query).limit(limit).to_df()
        # Instead of specifying columns, we return all data but the vector.
        results = results.drop(columns=['vector'])
        return results[results['_distance'] <= max_distance]
