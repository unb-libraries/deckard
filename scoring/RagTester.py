import time

from core.builders import build_llm_chain
from core.LLM import LLM
from core.prompts import CONTEXT_ONLY_PROMPT
from core.RagBuilder import RagBuilder
from core.utils import clear_gpu_memory
from scoring.RagConfigGenerator import RagConfigGenerator
from scoring.RagReporter import RagReporter
from secrets import token_hex

class RagTester:
    def __init__(self, log, config):
        self.log = log
        self.config = config

    def run(self):
        self.log.info("Running tests...")
        self.log.info("Loading LLM...")
        rag_configs = RagConfigGenerator("scoring/" + self.config['input'], self.log)

        llm = LLM(self.log, self.config['llm']['model']).get()
        prompt = CONTEXT_ONLY_PROMPT()

        reporter = RagReporter(self.config, self.log)
        for rag_configuration in rag_configs:
            configuration_id = token_hex(32)
            score = 0

            chain = build_llm_chain(
                llm,
                prompt
            )

            self.log.info(f"Building RAG data: {rag_configuration['name']}")
            builder = RagBuilder(rag_configuration, self.log)
            builder.build()

            self.log.info(f"Loading RAG stack: {rag_configuration['name']}")
            rag_stack = self.getRagStack(rag_configuration, self.log)

            self.log.info(f"Running queries RAG stack: {rag_configuration['name']}")
            question_responses = []
            question_response_times = []
            for test_query in self.config['test_queries']:
                now = time.time()
                response = rag_stack.query(
                    test_query['query'],
                    chain,
                    self.config['llm']['model']
                )
                response_time = time.time() - now
                question_response_times.append(response_time)
                if response == "":
                    response = "No response"
                    response_failed = True
                else:
                    if test_query['expected'] in response:
                        score += 1
                        response_failed = False
                    else:
                        response_failed = True

                question_responses.append({
                    "query": test_query['query'],
                    "expected": test_query['expected'],
                    "response": response,
                    "response_time": response_time,
                    "failed": response_failed
                })
            average_response_time = sum(question_response_times) / len(question_response_times)
            reporter.addScoreboardItem(
                configuration_id,
                rag_configuration['name'],
                score
            )
            reporter.addSummaryItem(
                configuration_id,
                rag_configuration['name'],
                score,
                question_responses,
                average_response_time
            )
            reporter.addDetailItem(
                configuration_id,
                rag_configuration['name'],
                score,
                {
                    "llm": self.config['llm']['model'],
                    "prompt": prompt,
                    "responses": question_responses
                }
            )
            reporter.addConfiguration(
                configuration_id,
                rag_configuration,
                score
            )

            del(builder)
            del(rag_stack)
            del(chain)
            clear_gpu_memory()

        reporter.writeReport()
        self.log.info("Tests complete.")

    def getRagStack(self, config, log):
        c = __import__(
            'core.' + config['stack']['classname'],
            fromlist=['']
        )
        rs = getattr(c, config['stack']['classname'])
        return rs(config, log)
