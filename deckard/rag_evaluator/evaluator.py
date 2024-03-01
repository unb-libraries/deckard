import time
from logging import Logger

from deckard.core.builders import build_llm_chain
from deckard.core.time import cur_timestamp
from deckard.core.utils import clear_gpu_memory
from deckard.core.utils import gen_uuid
from deckard.llm import CONTEXT_ONLY_PROMPT
from deckard.llm import LLM
from deckard.rag import RagBuilder

from .config_generator import RagConfigGenerator
from .reporter import RagEvaluatorReporter

class RagPipelineEvaluator:
    def __init__(
        self,
        log: Logger,
        config: dict
    ) -> None:
        self.log = log
        self.config = config

    def run(self) -> None:
        self.log.info("Running tests...")
        self.log.info("Loading LLM...")
        test_start = cur_timestamp()

        rag_configs = RagConfigGenerator("deckard/rag_evaluator/" + self.config['input'], self.log)

        llm = LLM(self.log, self.config['llm']['model']).get()
        prompt = CONTEXT_ONLY_PROMPT()

        reporter = RagEvaluatorReporter(self.config, self.log, test_start)
        for rag_configuration in rag_configs:
            configuration_id = gen_uuid()
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
                    if any(x.lower() in response.lower() for x in test_query['expected']):
                        response_failed = False
                        score += 1
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

    def getRagStack(
        self,
        config: dict,
        log: Logger
    ):
        c = __import__(
            config['stack']['module_name'],
            fromlist=['']
        )
        rs = getattr(c, config['stack']['class_name'])
        return rs(config, log)
