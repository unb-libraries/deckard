from json import dumps
from secrets import token_hex

from core.ResponseProcessor import ResponseProcessor
from core.QueryLoggerJsonFile import QueryLoggerJsonFile
from core.responses import error_response, fail_response

class LLMQuery:
    FAIL_RESPONSE_MESSAGE = fail_response()
    ERROR_RESPONSE_MESSAGE = error_response()

    def __init__(self, stack, id, client, llm_config):
        self.stack = stack
        self.log = stack.logger()
        self.workflow_id = id
        self.client = client
        self.llm_config = llm_config
        self.initQuery()

    def query(self, query, chain, start_time, lock_wait, safeguard = True):
        self.initQuery()
        self.log.info(f"New Query: {query} [{self.workflow_id}]")

        self.query_id = self.generateQueryID()
        self.log.info(f"Assigned ID: {self.query_id}")

        self.query_value = query
        self.log.info(f"Querying LLM: [{self.workflow_id}]")
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

    def logQuery(self, stack_response, tripwire_thrown, start_time, lock_wait):
        QueryLoggerJsonFile(
            self.query_id,
            self.client,
            self.query_value,
            stack_response,
            self.response,
            self.workflow_id,
            tripwire_thrown,
            self.response_metadata,
            start_time,
            lock_wait,
            self.response_fail
        ).write(self.query_id)

    def createQueryResponse(self):
        self.log.info(f"Responding with: {self.response}")
        return dumps({
            'response': self.response,
            'fail': self.response_fail
        })

    def generateQueryID(self):
        return token_hex(32)
