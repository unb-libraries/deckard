import json
import sys
import requests
import numpy as np
import uuid
import requests

from logging import Logger

from deckard.sparse.sparse_search import SparseSearch

class Solr(SparseSearch):
    """Provides a Solr interface for sparse query indexing and searching.

    The solr core requires a specific schema.

    Args:
        uri (str): The full URI to the core. For example, http://localhost:8983/solr/deckard.
        log (Logger): The logger for the database.
        create_if_not_exists (bool): Whether to create the database if it does not exist.

    Attributes:
        CONTEXT_TABLE_NAME (str): The name of the table for the context.
        DATA_PATH (str): The path to the data directory.
        log (Logger): The logger for the database.
        connection (sqlite3.Connection): The connection to the database.
    """

    def __init__(self,
            uri: str,
            log: Logger,
            create_if_not_exists: bool=False
        ) -> None:
        self.log = log
        self.log.info(f"Connecting to Solr: {uri}")
        self.indexer = SolrIndexer(solr_url=uri)
        self.client = SolrClient(solr_url=uri)

        # Check if the Solr core is accessible
        if not self.client.test_connection():
            self.log.error("Solr core is not accessible. Exiting.")
            sys.exit(1)

    def flush_data(self):
        self.client.flush_index()

    def index_document(self, document):
        self.indexer.index_document(document, commit=True)

class SolrIndexer:
    def __init__(self, solr_url="http://localhost:8983/solr/my_core"):
        self.solr_url = solr_url

    def index_document(self, document, commit=True):
        """Indexes a document into solr."""

        for idx, chunk in enumerate(document['raw_chunks']):
            doc = {
                "id": str(uuid.uuid4()),
                "document_id": document['id'],
                "chunk_id": idx,
                "document": chunk,
                "metadata": json.dumps(document['metadata'])
            }
            response = requests.post(f"{self.solr_url}/update", json=[doc])

        # Commit only if explicitly requested
        if commit:
            self.commit()

        return response.json()

    def commit(self):
        """Explicitly commits pending changes in Solr."""
        response = requests.get(f"{self.solr_url}/update?commit=true")
        return response.json()

    def delete_document(self, document_id, commit=True):
        """Deletes a document from Solr by document_id with optional commit."""
        delete_query = {"delete": {"query": f"document_id:{document_id}"}}
        response = requests.post(f"{self.solr_url}/update", json=delete_query)

        # Commit only if explicitly requested
        if commit:
            self.commit()

        return response.json()
    

class SolrClient:
    def __init__(self, solr_url="http://localhost:8983/solr/my_core", ngram_min=3, ngram_max=10):
        self.solr_url = solr_url
        self.ngram_min = ngram_min
        self.ngram_max = ngram_max

    def _generate_ngrams(self, text):
        """Generates a list of n-grams from the query text."""
        text = text.lower()
        ngrams = set()

        for size in range(self.ngram_min, min(len(text), self.ngram_max) + 1):
            for i in range(len(text) - size + 1):
                ngrams.add(text[i : i + size])

        return list(ngrams)

    def test_connection(self):
        """Tests the Solr connection by checking if the core is accessible."""
        try:
            response = requests.get(f"{self.solr_url}/admin/ping", timeout=5)
            if response.status_code == 200:
                return True
            else:
                print(f"Solr responded with status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            return False

    def search(self, query, top_n=10, exact_boost=3.0):
        """Searches both document (boosted) and document_ngram fields."""
        # Generate n-grams from the query
        ngram_tokens = self._generate_ngrams(query)
        ngram_query = " OR ".join([f'document_ngram:"{token}"' for token in ngram_tokens])

        # Solr query
        solr_query = {
            "q": f'document:"{query}"^{exact_boost} OR ({ngram_query})',
            "fl": "id,document_id,chunk_id,document,score",
            "rows": top_n
        }

        response = requests.get(f"{self.solr_url}/select", params=solr_query)
        results = response.json().get("response", {}).get("docs", [])

        if not results:
            return []

        scores = np.array([doc["score"] for doc in results])
        normalized_scores = scores / np.max(scores)
        
        for i, doc in enumerate(results):
            doc["normalized_score"] = round(float(normalized_scores[i]), 4)

        return results

    def flush_index(self):
        """Deletes all indexed documents from Solr."""
        delete_query = {"delete": {"query": "*:*"}}  # Delete everything
        response = requests.post(f"{self.solr_url}/update?commit=true", json=delete_query)
        return response.json()
