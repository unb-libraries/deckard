from langchain.chains import LLMChain

from deckard.core import json_dumper
from deckard.core.utils import gen_uuid
from deckard.query_loggers import QueryLoggerJsonFile
from deckard.rag import RagStack

from .response_processor import ResponseProcessor
from .responses import error_response, fail_response

class LLMQuery:
    FAIL_RESPONSE_MESSAGE = fail_response()
    ERROR_RESPONSE_MESSAGE = error_response()

    def __init__(
        self,
        stack: RagStack,
        id: str,
        client: str,
        llm_config: dict
    ) -> None:
        self.stack = stack
        self.log = stack.logger()
        self.pipeline_id = id
        self.client = client
        self.llm_config = llm_config
        self.initQuery()

    def query(
        self,
        query: str,
        chain: LLMChain,
        start_time: float,
        lock_wait: float,
        safeguard: bool=True
    ) -> str:
        self.initQuery()
        self.log.info(f"New Query: {query} [{self.pipeline_id}]")

        self.query_id = gen_uuid()
        self.log.info(f"Assigned ID: {self.query_id}")

        self.query_value = query
        self.log.info(f"Querying LLM: [{self.pipeline_id}]")
        stack_response = self.stack.query(query, chain, self.llm_config)
        self.response_metadata.append(self.stack.getResponseMetadata())

        if self.stack.getResponseFail():
            if self.stack.getResponse() == '':
                self.response = self.ERROR_RESPONSE_MESSAGE
            self.response_fail = True

        processor = ResponseProcessor(stack_response)
        tripwire_thrown = processor.tripWireThrown()
        if safeguard and tripwire_thrown:
            self.response = self.FAIL_RESPONSE_MESSAGE
            self.response_fail = True
            self.log.info(f"Tripwire thrown, responding with: {self.response}")
        else:
            self.response = processor.getResponse()

        self.logQuery(stack_response, tripwire_thrown, start_time, lock_wait)
        return self.createQueryResponse()

    def initQuery(self):
        self.query_value = ''
        self.response = ''
        self.response_fail = False
        self.response_metadata = []

    def logQuery(
        self,
        stack_response: str,
        tripwire_thrown: bool,
        start_time: float,
        lock_wait: float
    ) -> None:
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

    def createQueryResponse(self) -> str:
        self.log.info(f"Responding with: {self.response}")
        return json_dumper({
            'response': self.response,
            'fail': self.response_fail
        })

