from core.classloader import load_class


class RagStack:
    MAX_CONTEXTS = 25
    NO_CONTEX_RESPONSE = "Sorry, this question doesn't seem to be answered within the information I was provided."

    def __init__(self, config, log):
        self.log = log
        self.config = config
        self.log.info(f"Building RAG Stack for configuration: {config['name']}")
        self.initComponents()

    def logger(self):
        return self.log

    def addConfigToResponseMetadata(self):
        self.response_metadata.append({'configuration': self.config})
        self.response_metadata.append({'api_llm': self.llm_config})

    def query(self, query, chain, llm_config):
        self.initQuery()
        self.query_value = query
        self.llm_config = llm_config
        self.chain = chain

        self.query_processor.setQuery(query)
        embedding_query = self.query_processor.getEmbeddingSearchQuery()

        self.log.info(f"Generating embedding for query: {query} ({embedding_query}) [{self.workflow_id}]")
        query_vector = self.encoder.encode(embedding_query)

        self.log.info(f"Querying Vector Database with embeddings: {query} [{self.workflow_id}]")
        vec_results = self.database.query(
            query_vector,
            limit=self.MAX_CONTEXTS,
            max_distance=self.context_max_distance,
        )

        self.log.info(f"Reranking Results: {query} ({embedding_query}) [{self.workflow_id}]")
        reranked_results = self.reranker.rerank(embedding_query, vec_results)

        self.log.info(f"Generating context for query: {query} [{self.workflow_id}]")
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

        self.log.info(f"Querying Chain for query: {query} [{self.workflow_id}]")
        self.queryChain()
        return self.response

    def search(self, query):
        self.log.info(f"Generating embedding for query: {query} [{self.workflow_id}]")
        query_vector = self.encoder.encode(query)

        self.log.info(f"Querying Vector Database with embeddings: {query} [{self.workflow_id}]")
        vec_results = self.database.query(
            query_vector,
            limit=self.MAX_CONTEXTS,
            max_distance=self.context_max_distance,
        )
        vec_results = vec_results.drop(columns=['vector'])
        return(vec_results)

    def initQuery(self):
        self.query_value = ''
        self.chain = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = []

    def queryChain(self):
        chain_reponse = self.chain.invoke(
            {
                "context": self.context,
                "query": self.query_value
            }
        )
        self.response = chain_reponse['text']

    def getResponse(self):
        return self.response

    def getResponseMetadata(self):
        return self.response_metadata

    def getResponseFail(self):
        return self.response_fail

    def initComponents(self):
        self.encoder = load_class(
            'encoders',
            self.config['embedding_encoder']['class'],
            [
                self.config['embedding_encoder']['model'],
                self.log
            ]
        )
        self.reranker = load_class(
            'encoders',
            self.config['reranker']['class'],
            [
                self.config['reranker']['model'],
                self.log
            ]
        )
        self.database = load_class(
            'vectordatabases',
            self.config['embedding_database']['class'],
            [
                self.config['embedding_database']['name'],
                self.log,
                True
            ]
        )
        self.context_database = load_class(
            'contextdatabases',
            self.config['context_database']['class'],
            [
                self.config['context_database']['name'],
                self.log,
                True
            ]
        )
        self.context_builder = load_class(
            'contextbuilders',
            self.config['context_builder']['class'],
            [
                self.log
            ]
        )

        self.query_processor = load_class(
            'queryprocessors',
            self.config['query_processor']['class'],
            [
                self.log
            ]
        )

        self.context_size = self.config['context']['size']
        self.context_max_distance = self.config['context']['max_vector_distance']
        self.workflow_id = self.config['name']
