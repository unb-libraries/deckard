from langchain.chains import LLMChain
from logging import Logger
from pandas import DataFrame

from deckard.core import load_class

class RagStack:
    """Provides a class that intefaces with a RAG pipeline.

    Args:
        config (dict): The pipeline configuration.
        log (Logger): The logger.

    Attributes:
        NO_CONTEX_RESPONSE (str): The response for no context found.
        chain (str): The chain for the query.
        config (dict): The configuration.
        context (str): The context for the query.
        context_builder (ContextBuilder): The context builder.
        context_database (ContextDatabase): The context database.
        context_max_distance (float): The maximum distance for the context.
        context_size (int): The size of the context.
        database (EmbeddingDatabase): The database for the embeddings.
        encoder (EmbeddingEncoder): The encoder for the embeddings.
        llm_config (dict): The LLM configuration.
        log (Logger): The logger.
        pipeline_id (str): The pipeline ID.
        query_processor (QueryProcessor): The query processor.
        response (str): The response.
        response_fail (bool): The response fail flag.
        response_metadata (list): The response metadata.
        reranker (Reranker): The reranker for the embeddings.
    """

    NO_CONTEX_RESPONSE = "Sorry, this question doesn't seem to be answered within the information I was provided."
    MAX_CONTEXTS = 10

    def __init__(
        self,
        config: dict,
        log: Logger
    ) -> None:
        self.log = log
        self.config = config
        self.log.info("Building RAG Stack for configuration: %s", config['name'])
        self.init_query()
        self._init_rag_pipeline_components()
        self.chain = ''
        self.context = ''
        self.query_value = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = []
        self.llm_config = {}


    def logger(self) -> Logger:
        """Returns the logger.

        Returns:
            Logger: The logger.
        """
        return self.log

    def add_config_response_metadata(self) -> None:
        """Adds the RAG configuration to the response metadata."""
        self.response_metadata.append({'configuration': self.config})
        self.response_metadata.append({'api_llm': self.llm_config})

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

        self.query_processor.set_query(query)
        embedding_query = self.query_processor.get_embedding_search_query()

        self.log.info("Generating embedding for query: %s (%s) [%s]", query, embedding_query, self.pipeline_id)
        query_vector = self.encoder.encode(embedding_query)

        self.log.info("Querying Vector Database with embeddings: %s [%s] (Max Distance: %s)", query, self.pipeline_id, self.context_max_distance)
        vec_results = self.database.query(
            query_vector,
            limit=self.config['reranker']['max_raw_results'],
            max_distance=self.context_max_distance,
        )

        self.log.info("Reranking Results: %s (%s) [%s]", query, embedding_query, self.pipeline_id)
        reranked_results = self.reranker.rerank(embedding_query, vec_results)

        self.log.info("Querying Sparse Search for query: %s [%s]", query, self.pipeline_id)
        sparse_results = self.sparse_search.search(embedding_query)

        self.log.info("Generating context for query: %s [%s]", query, self.pipeline_id)
        self.context, context_metadata = self.context_builder.build_context(
            reranked_results,
            sparse_results,
            self.context_database,
            self.context_size
        )

        self.response_metadata.append({'embedding_query': embedding_query})
        self.response_metadata.append({'vector_results': reranked_results.to_dict()})
        self.response_metadata.append({'sparse_results': sparse_results})
        self.response_metadata.append(context_metadata)
        self.add_config_response_metadata()

        if self.context == '':
            self.response = self.NO_CONTEX_RESPONSE
            self.response_fail = True
            self.log.info("No Context Found for query: %s, Responding with: %s", query, self.response)
            return self.response

        self.log.info("Querying Chain for query: %s [%s]", query, self.pipeline_id)
        self.query_chain()

        return self.response

    def search(self, query: str) -> DataFrame:
        """Searches the embeddings database.

        Args:
            query (str): The query.

        Returns:
            DataFrame: The search results.
        """
        self.log.info("Generating embedding for query: %s [%s]", query, self.pipeline_id)
        query_vector = self.encoder.encode(query)

        self.log.info("Querying Vector Database with embeddings: %s [%s]", query, self.pipeline_id)
        vec_results = self.database.query(
            query_vector,
            limit=self.MAX_CONTEXTS,
            max_distance=self.context_max_distance,
        )
        return vec_results

    def init_query(self) -> None:
        """Initializes the query."""
        self.chain = ''
        self.context = ''
        self.query_value = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = []
        self.llm_config = {}

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

    def _init_rag_pipeline_components(self) -> None:
        """Initializes the components for the RAG pipeline."""
        self.encoder = load_class(
            self.config['embedding_encoder']['module_name'],
            self.config['embedding_encoder']['class_name'],
            [
                self.config['embedding_encoder']['model'],
                self.log
            ]
        )
        self.reranker = load_class(
            self.config['reranker']['module_name'],
            self.config['reranker']['class_name'],
            [
                self.config['reranker']['model'],
                self.log
            ]
        )
        self.database = load_class(
            self.config['embedding_database']['module_name'],
            self.config['embedding_database']['class_name'],
            [
                self.config['embedding_database']['name'],
                self.log,
                True
            ]
        )
        self.context_database = load_class(
            self.config['context_database']['module_name'],
            self.config['context_database']['class_name'],
            [
                self.config['context_database']['name'],
                self.log,
                True
            ]
        )

        self.sparse_search = load_class(
            self.config['sparse_search']['module_name'],
            self.config['sparse_search']['class_name'],
            [
                self.config['sparse_search']['uri'],
                self.log,
                True
            ]
        )

        self.context_builder = load_class(
            self.config['context_builder']['module_name'],
            self.config['context_builder']['class_name'],
            [
                self.log
            ]
        )

        self.query_processor = load_class(
            self.config['query_processor']['module_name'],
            self.config['query_processor']['class_name'],
            [
                self.log
            ]
        )

        self.context_size = self.config['context']['size']
        self.context_max_distance = self.config['context']['max_vector_distance']
        self.pipeline_id = self.config['name']
