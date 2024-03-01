from logging import Logger

from langchain.chains import LLMChain
from pandas import DataFrame

from deckard.core import load_class

class RagStack:
    MAX_CONTEXTS = 25
    NO_CONTEX_RESPONSE = "Sorry, this question doesn't seem to be answered within the information I was provided."

    def __init__(
        self,
        config: dict,
        log: Logger
    ) -> None:
        self.log = log
        self.config = config
        self.log.info(f"Building RAG Stack for configuration: {config['name']}")
        self.initComponents()

    def logger(self) -> Logger:
        return self.log

    def addConfigToResponseMetadata(self) -> None:
        self.response_metadata.append({'configuration': self.config})
        self.response_metadata.append({'api_llm': self.llm_config})

    def query(
        self,
        query: str,
        chain: LLMChain,
        llm_config: dict
    ) -> str:
        self.initQuery()
        self.query_value = query
        self.llm_config = llm_config
        self.chain = chain

        self.query_processor.setQuery(query)
        embedding_query = self.query_processor.getEmbeddingSearchQuery()

        self.log.info(f"Generating embedding for query: {query} ({embedding_query}) [{self.pipeline_id}]")
        query_vector = self.encoder.encode(embedding_query)

        self.log.info(f"Querying Vector Database with embeddings: {query} [{self.pipeline_id}]")
        vec_results = self.database.query(
            query_vector,
            limit=self.MAX_CONTEXTS,
            max_distance=self.context_max_distance,
        )

        self.log.info(f"Reranking Results: {query} ({embedding_query}) [{self.pipeline_id}]")
        reranked_results = self.reranker.rerank(embedding_query, vec_results)

        self.log.info(f"Generating context for query: {query} [{self.pipeline_id}]")
        self.context, context_metadata = self.context_builder.buildContext(
            reranked_results,
            self.context_database,
            self.context_size
        )

        self.response_metadata.append({'embedding_query': embedding_query})
        self.response_metadata.append({'vector_results': reranked_results.to_dict()})
        self.response_metadata.append(context_metadata)
        self.addConfigToResponseMetadata()

        if self.context == '':
            self.response = self.NO_CONTEX_RESPONSE
            self.response_fail = True
            self.log.info(f"No Context Found for query: {query}, Responding with: {self.response}")
            return self.response

        self.log.info(f"Querying Chain for query: {query} [{self.pipeline_id}]")
        self.queryChain()
        return self.response

    def search(self, query: str) -> DataFrame:
        self.log.info(f"Generating embedding for query: {query} [{self.pipeline_id}]")
        query_vector = self.encoder.encode(query)

        self.log.info(f"Querying Vector Database with embeddings: {query} [{self.pipeline_id}]")
        vec_results = self.database.query(
            query_vector,
            limit=self.MAX_CONTEXTS,
            max_distance=self.context_max_distance,
        )
        vec_results = vec_results.drop(columns=['vector'])
        return(vec_results)

    def initQuery(self) -> None:
        self.query_value = ''
        self.chain = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = []

    def queryChain(self) -> None:
        chain_reponse = self.chain.invoke(
            {
                "context": self.context,
                "query": self.query_value
            }
        )
        self.response = chain_reponse['text']

    def getResponse(self) -> str:
        return self.response

    def getResponseMetadata(self) -> dict:
        return self.response_metadata

    def getResponseFail(self) -> bool:
        return self.response_fail

    def initComponents(self) -> None:
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
