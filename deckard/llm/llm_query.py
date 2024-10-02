""" Provides the LLMQuery class. """
from logging import Logger

from langchain.chains import LLMChain

from deckard.core import json_dumper
from deckard.core.utils import gen_uuid, short_uuid
from deckard.query_loggers import QueryLoggerJsonFile
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
        response_metadata (list): The response metadata.
        stack (RagStack): The RAG stack to use.
    """
    FAIL_RESPONSE_MESSAGE = fail_response()
    ERROR_RESPONSE_MESSAGE = error_response()

    def __init__(
        self,
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
        self.query_id = gen_uuid()
        self.query_value = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = []

    def query(
        self,
        query: str,
        chain: LLMChain,
        start_time: float,
        lock_wait: float,
        safeguard: bool=True
    ) -> str:
        """ Queries the LLM chain.

        Args:
            query (str): The query to use.
            chain (LLMChain): The LLM chain to use.
            start_time (float): The time the query was recieved.
            lock_wait (float): The time the query waited for the GPU lock.
            safeguard (bool, optional): Whether to safeguard the query against
                      Potentially offensive responses. Defaults to True.

        Returns:
            str: The query response.
        """
        self.log.info("New Query: %s [%s]", query, self.pipeline_id)
        self.log.info("Assigned ID: %s", short_uuid(self.query_id))

        self.query_value = query
        self.log.info("Querying LLM: [%s]", self.pipeline_id)
        stack_response = self.stack.query(query, chain, self.llm_config)
        self.response_metadata.append(self.stack.get_response_metadata())

        if self.stack.get_response_fail():
            if self.stack.get_response() == '':
                self.response = self.ERROR_RESPONSE_MESSAGE
            self.response_fail = True

        processor = ResponseProcessor(stack_response)
        tripwire_thrown = processor.was_tripwire_thrown()
        if safeguard and tripwire_thrown:
            self.response = self.FAIL_RESPONSE_MESSAGE
            self.response_fail = True
            self.log.info("Tripwire thrown, responding with: %s", self.response)
        else:
            self.response = processor.get_clean_response()

        self._log_query(stack_response, tripwire_thrown, start_time, lock_wait)
        return self._build_query_reponse()

    def _log_query(
        self,
        stack_response: str,
        tripwire_thrown: bool,
        start_time: float,
        lock_wait: float
    ) -> None:
        """Logs the query.

        Args:
            stack_response (str): The stack response.
            tripwire_thrown (bool): Whether the tripwire was thrown.
            start_time (float): The time the query was recieved.
            lock_wait (float): The time the query waited for the GPU lock.
        """
        QueryLoggerJsonFile(
            self.query_id,
            self.client,
            self.query_value,
            stack_response,
            self.response,
            self.pipeline_id,
            tripwire_thrown,
            self.response_metadata,
            start_time,
            lock_wait,
            self.response_fail
        ).write(self.query_id)

    def _build_query_reponse(self) -> str:
        """Creates the query response.

        Returns:
            str: The query response as a JSON string.
        """
        self.log.info("Responding with: %s", self.response)
        return json_dumper({
            'response': self.response,
            'fail': self.response_fail,
            'metadata': self.response_metadata
        })
