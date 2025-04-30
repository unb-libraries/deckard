from langchain.chains import LLMChain
from logging import Logger
from pandas import DataFrame

from deckard.core import load_class, make_json_safe
from deckard.llm import QAResponder

class QAStack:
    def __init__(
        self,
        config: dict,
        log: Logger
    ) -> None:
        self.log = log
        self.config = config
        self.log.info("Building QA Stack for configuration: %s", config['name'])
        self.init_query()
        self._init_qa_pipeline_components()
        self.chain = ''
        self.context = ''
        self.query_value = ''
        self.matching_qa_questions = []
        self.response = ''
        self.response_fail = False
        self.response_metadata = {}
        self.llm_config = {}

    def has_questions(self) -> bool:
        """Checks if the QA stack has questions.

        Returns:
            bool: True if the stack has questions, False otherwise.
        """
        if not self.config:
            self.log.warning("QA stack has no config.")
            return False
        return len(self.config['questions']) > 0

    def logger(self) -> Logger:
        """Returns the logger.

        Returns:
            Logger: The logger.
        """
        return self.log

    def add_config_response_metadata(self) -> None:
        """Adds the RAG configuration to the response metadata."""
        self.response_metadata.update({'configuration': self.config})
        self.response_metadata.update({'api_llm': self.llm_config})

    def query(
        self,
        query: str,
        chain: LLMChain,
        llm_config: dict
    ) -> str:
        """Queries the RAG pipeline.

        Args:
            query (str): The query.
            chain (LLMChain): The chain for the query.
            llm_config (dict): The LLM configuration.

        Returns:
            str: The response.
        """
        self.init_query()
        self.query_value = query
        self.llm_config = llm_config
        self.chain = chain

        self.log.info("Generating embedding for WA query: %s [%s]", query, self.pipeline_id)
        query_vector = self.qa_encoder.encode(query)

        self.log.info("Querying QA Database with embeddings: %s [%s] (Max Distance: %s)", query, self.pipeline_id, self.qa_max_distance)
        vec_results = self.qa_database.query(
            query_vector,
            limit=self.top_k,
            max_distance=self.qa_max_distance,
        )

        self.matching_qa_questions = vec_results
        if len(vec_results) == 0:
            self.log.warning("No matching questions found in QA Database for query: %s", query)
            self.response_fail = True
            self.response = {
                'has_response': False,
                'response': '',
                'response_metadata': self.response_metadata,
                'links': []
            }
            return self.response

        self.log.info("Found %s matching questions for query: %s", len(vec_results), query)
        # ['id', 'response', 'links', 'query', '_distance']
        vec_results_metadata = vec_results.to_dict(orient='records')
        self.response_metadata.update({'vector_results': make_json_safe(vec_results_metadata)})

        # drop the id and _distance columns.
        vec_results = vec_results.drop(columns=['id', '_distance'])
        results_json = vec_results.to_json(orient='records')

        self.log.info("Vector results converted to JSON data: %s", results_json)

        responder = QAResponder(self.chain, self.log)
        has_response, response_text, links = responder.query_responder(query, results_json)

        self.response = {
            'has_response': has_response,
            'response': response_text,
            'metadata': self.response_metadata,
            'links': links
        }
        return self.response

    def search(self, query: str) -> DataFrame:
        """Searches the embeddings database.

        Args:
            query (str): The query.

        Returns:
            DataFrame: The search results.
        """
        self.log.info("Generating QA embedding for query: %s [%s]", query, self.pipeline_id)
        query_vector = self.encoder.encode(query)

        self.log.info("Querying QA Vector Database with embeddings: %s [%s]", query, self.pipeline_id)
        vec_results = self.database.query(
            query_vector,
            limit=self.top_k,
            max_distance=self.max_distance,
        )
        return vec_results

    def init_query(self) -> None:
        """Initializes the query."""
        self.chain = ''
        self.query_value = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = {}
        self.qa_config = {}

    def query_chain(self) -> None:
        """Queries the LLM chain."""
        chain_response = self.chain.invoke(
            {
                "context": self.context,
                "query": self.query_value
            }
        )
        self.response = chain_response

    def get_response(self) -> str:
        """Returns the response.

        Returns:
            str: The response.
        """
        return self.response

    def get_response_metadata(self) -> dict:
        """Returns the response metadata.

        Returns:
            dict: The response metadata.
        """
        return self.response_metadata

    def get_response_fail(self) -> bool:
        """Returns whether the query failed.

        Returns:
            bool: Whether the query failed.
        """
        return self.response_fail

    def _init_qa_pipeline_components(self) -> None:
        """Initializes the components for the RAG pipeline."""
        self.qa_encoder = load_class(
            self.config['encoder']['module_name'],
            self.config['encoder']['class_name'],
            [
                self.config['encoder']['model'],
                self.log
            ]
        )
        self.qa_database = load_class(
            self.config['database']['module_name'],
            self.config['database']['class_name'],
            [
                self.config['database']['name'],
                self.log,
                True
            ]
        )

        self.top_k = int(self.config['top_k'])
        self.qa_max_distance = self.config['max_distance']
        self.pipeline_id = self.config['name']
