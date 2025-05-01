"""Provides a LanceDB interface for adding and querying embeddings."""
import os
import sys
from logging import Logger
from typing import TypeVar

import lancedb
import pyarrow as pa
import pandas as pd
from lance.vector import vec_to_table

from deckard.core import get_data_dir

T = TypeVar('T', dict, list, int)

class LanceDB:
    """Provides a LanceDB interface for adding and querying embeddings.

    Args:
        name (str): The name of the database.
        log (Logger): The logger for the database.

    Attributes:
        EMBEDDINGS_TABLE_NAME (str): The name of the table for the embeddings.
        DATA_PATH (str): The path to the data directory.
        name (str): The name of the database.
        log (Logger): The logger for the database.
        create_if_not_exists (bool): Whether to create the database if it does not exist.
        connection (lancedb.Connection): The connection to the database.
        embeddings_table (lancedb.Table): The table for the embeddings.
    """

    EMBEDDINGS_TABLE_NAME = "llm_embeddings"
    DATA_PATH = os.path.join(
        get_data_dir(),
        'databases',
        'lancedb'
    )

    def __init__(
            self,
            name: str,
            log: Logger,
            create_if_not_exists: bool=False
        ) -> None:
        self.log = log
        db_filepath = os.path.join(self.DATA_PATH, '.' + name)
        if not os.path.exists(self.DATA_PATH):
            if create_if_not_exists:
                self.log.info("Creating Database Path: %s", name)
                os.makedirs(self.DATA_PATH)
            else:
                self.log.error("Database path does not exist.")
                sys.exit(1)
        self.log.info(f"Connecting to Database: {name}")
        self.connection = lancedb.connect(db_filepath)
        try:
            self.embeddings_table = self.connection.open_table(self.EMBEDDINGS_TABLE_NAME)
        except Exception:
            self.log.warning("Table: %s does not exist.", self.EMBEDDINGS_TABLE_NAME)

    def flush_data(self):
        """Flushes all data from the embeddings table."""
        self.connection.drop_table(
            self.EMBEDDINGS_TABLE_NAME,
            ignore_missing=True
        )

    def _create_table(self, data: dict):
        """Creates the embeddings table in the database

        Args:
            data (str): The data to create the table with.
        """
        self.embeddings_table = self.connection.create_table(
            self.EMBEDDINGS_TABLE_NAME,
            data=data,
            mode="overwrite"
        )

    ## Embedding Methods
    ##
    def add_embeddings(
            self,
            document: list,
            embedding_id_start: int,
            create_table: bool=False
        ) -> int:
        """Adds embeddings to lancedb.

        Args:
            document (dict): The document's data to add to the database. Each
                     document should have the following elements:
                        - id: The document's ID.
                        - raw_chunks list(str): The raw chunks of the document.
                        - embeddings list(Tensor): The embeddings of the document.
            embedding_id_start (int): The starting embedding id.
            create_table (bool): Whether to create the table if it does not exist.

        Returns:
            int: The highest embedding id inserted
        """
        item_metadata, embeddings, embedding_id = self._build_database_values_for_document(
            document,
            embedding_id_start
        )

        # Blend the metadata and embeddings into a single table
        textual_data = pa.Table.from_pydict(item_metadata)
        et = vec_to_table(embeddings)
        items = textual_data.append_column("vector", et["vector"])

        self.log.info("Adding document %s %s embeddings to LanceDB.", document['id'], len(embeddings))
        if create_table:
            self._create_table(items)
        else:
            self.embeddings_table.add(items)
        return embedding_id

    def _build_database_values_for_document(
            self,
            document: dict,
            embedding_id_start: int
        ) -> T:
        """Builds the values to be inserted into the database for a document.

        Args:
            document (dict): The document's data to add to the database. Each
                     document should have the following elements:
                        - id: The document's ID.
                        - raw_chunks list(str): The raw chunks of the document.
                        - embeddings list(Tensor): The embeddings of the document.
            embedding_id_start (int): The starting embedding id.

        Returns:
            T: The item metadata, embeddings, and the highest embedding id inserted
        """
        embedding_id = embedding_id_start
        ids = []
        doc_ids = []
        chunk_ids = []
        texts = []
        embeddings = []
        metadata = []

        for idx, embedding in enumerate(document['embeddings']):
            embedding_id += 1
            ids.append(embedding_id)
            doc_ids.append(document['id'])
            chunk_ids.append(idx)
            texts.append(document['raw_chunks'][idx])
            embeddings.append(embedding)
            metadata.append(document['metadata'])

        item_metadata = {
            'id': ids,
            'text': texts,
            'doc_id': doc_ids,
            'chunk_id': chunk_ids,
            'metadata': metadata
        }

        return item_metadata, embeddings, embedding_id

    def query(
            self,
            query: str,
            limit: int=25,
            max_distance: int=5
        ) -> list:
        """Queries the database for embedding similarity.

        Args:
            query (str): The query to search for.
            limit (int): The maximum number of results to return.
            max_distance (int): The maximum distance to return.

        Returns:
            list: The results of the query.
        """
        results = self.embeddings_table.search(query).distance_range(upper_bound=max_distance).limit(limit).to_df()
        # results = self.embeddings_table.search(query).distance_range(upper_bound=max_distance).to_df()
        # Instead of specifying columns, we return all data but the vector.
        results = results.drop(columns=['vector'])
        return results

    ## QA Methods
    ##
    def add_qa_question(
            self,
            question_metadata: dict,
            create_table: bool=False
        ) -> None:

        # NOTE: Each value is wrapped in a list to form a 1-row DataFrame.
        # This ensures all columns have equal-length arrays, as required by Pandas and LanceDB.
        # Without this, you'll get "ValueError: All arrays must be of the same length".
        # See: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
        for key in question_metadata:
            question_metadata[key] = [question_metadata[key]]

        # OLD data = pa.Table.from_pydict(question_metadata)
        df = pd.DataFrame(question_metadata)

        self.log.info("Adding question %s to LanceDB.", df)
        if create_table:
            self._create_table(df)
        else:
            self.embeddings_table.add(df)
 
    def question_query(
            self,
            query: str,
            limit: int=25,
            max_distance: int=5
        ) -> list:
        """Queries the database for embedding similarity.

        Args:
            query (str): The query to search for.
            limit (int): The maximum number of results to return.
            max_distance (int): The maximum distance to return.

        Returns:
            list: The results of the query.
        """
        results = self.embeddings_table.search(query).distance_range(upper_bound=max_distance).limit(limit).to_df()
        # results = self.embeddings_table.search(query).distance_range(upper_bound=max_distance).to_df()
        # Instead of specifying columns, we return all data but the vector.
        results = results.drop(columns=['vector'])
        return results

    def has_qa_data(self) -> bool:
        """Checks if the QA table exists and has at least one row."""
        try:
            if not self.embeddings_table:
                self.log.warning("Embeddings table does not exist.")
                return False

            # Check if the table has at least one row
            return self.embeddings_table.count_rows() > 0
        except Exception as e:
            self.log.error("Error checking QA data: %s", str(e))
            return False