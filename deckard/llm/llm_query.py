""" Provides the LLMQuery class. """
from logging import Logger

from langchain.chains import LLMChain

from deckard.core.utils import gen_uuid, short_uuid
from deckard.rag import RagStack
from .response_processor import ResponseProcessor
from .responses import error_response, fail_response

class LLMQuery:
    """The LLMQuery class provides a query interface to the LLM.

    Args:
        stack (RagStack): The RAG stack to use.
        pipeline_id (str): The pipeline ID to use.
        client (str): The client name requesting the query.
        llm_config (dict): The LLM configuration to use.

    Attributes:
        ERROR_RESPONSE_MESSAGE (str): The error response message.
        FAIL_RESPONSE_MESSAGE (str): The fail response message.
        client (str): The client name requesting the query.
        llm_config (dict): The LLM configuration to use.
        log (Logger): The logger to use.
        pipeline_id (str): The pipeline ID to use.
        query (str): The query.
        query_id (str): The query ID.
        query_value (str): The query value.
        response (str): The response.
        response_fail (bool): The response fail flag.
        response_metadata (dict): The response metadata.
        stack (RagStack): The RAG stack to use.
    """
    FAIL_RESPONSE_MESSAGE = fail_response()
    ERROR_RESPONSE_MESSAGE = error_response()

    def __init__(
        self,
        query_id: str,
        stack: RagStack,
        pipeline_id: str,
        client: str,
        llm_config: dict,
        log: Logger
    ) -> None:
        self.log = log
        self.stack = stack
        self.pipeline_id = pipeline_id
        self.client = client
        self.llm_config = llm_config
        self.query_id = query_id
        self.query_value = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = {}

    def query(
        self,
        query: str,
        chain: LLMChain,
    ) -> str:
        """ Queries the LLM chain.

        Args:
            query (str): The query to use.
            chain (LLMChain): The LLM chain to use.

        Returns:
            str: The query response.
        """
        self.query_value = query
        self.log.info("New Query: %s [%s]: %s", query, self.pipeline_id, short_uuid(self.query_id))
        stack_response = self.stack.query(query, chain, self.llm_config)

        self.response_metadata.update(self.stack.get_response_metadata())

        if self.stack.get_response_fail():
            if self.stack.get_response() == '':
                self.response = self.ERROR_RESPONSE_MESSAGE
            self.response_fail = True

        processor = ResponseProcessor(stack_response)
        self.response = processor.get_clean_response()

        response = {
            'id': self.query_id,
            'client': self.client,
            'query': self.query_value,
            'response': self.response,
            'stack_response': stack_response,
            'pipeline': self.pipeline_id,
            'metadata': self.response_metadata
        }

        if self.response_fail:
            response['error'] = self.response
        
        return response
