from core.config import get_api_llm_config
from core.config import get_workflow
from core.config import get_workflow_context_db
from core.config import get_workflow_context_rag_conf
from core.config import get_workflow_db
from core.config import get_workflow_query_processor
from core.config import get_workflow_rag_context_builder
from core.config import get_workflow_rag_reranker
from core.config import get_workflow_encoder

class RagStack:
    MAX_CONTEXTS = 25
    NO_CONTEX_RESPONSE = "Sorry, this question doesn't seem to be answered within the information I was provided."

    def __init__(self, workflow_id, log, only_context=False):
        self.log = log
        self.log.info(f"Building RAG Stack for workflow: {workflow_id}")

        self.encoder = get_workflow_encoder(workflow_id, log)
        self.reranker = get_workflow_rag_reranker(workflow_id, log)
        self.database = get_workflow_db(workflow_id, log)
        self.context_database = get_workflow_context_db(workflow_id, log)
        self.context_builder = get_workflow_rag_context_builder(workflow_id, log)
        rag_conf = get_workflow_context_rag_conf(workflow_id)

        self.context_size = rag_conf['context_size']
        self.context_max_distance = float(rag_conf['max_context_distance'])
        self.workflow_id = workflow_id
        self.only_context = only_context

    def logger(self):
        return self.log

    def addWorkflowConfigToResponseMetadata(self):
        self.response_metadata.append({'workflow': get_workflow(self.workflow_id)})
        self.response_metadata.append({'api_llm': get_api_llm_config()})

    def query(self, query, chain):
        self.initQuery()
        self.query_value = query
        self.chain = chain

        query_processor = get_workflow_query_processor(self.workflow_id, query, self.log)
        embedding_query = query_processor.getEmbeddingSearchQuery()

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
        self.addWorkflowConfigToResponseMetadata()

        if self.context == '' and self.only_context:
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
