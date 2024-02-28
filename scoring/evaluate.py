import yaml

from core.logger import get_logger
from core.builders import build_llm_chain
from core.prompts import CONTEXT_ONLY_PROMPT
from core.LLM import LLM
from core.RagBuilder import RagBuilder

def start():
    log = get_logger()
    log.info("Starting...")

    config = yaml.safe_load(open("scoring/config.yml"))
    tests = RagTester(
        log,
        config['evaluate']
    )
    tests.run()

class RagTester:
    def __init__(self, log, config):
        self.log = log
        self.config = config
        self.report = []

    def run(self):
        self.log.info("Running tests...")
        self.log.info("Loading LLM...")

        llm = LLM(self.log, self.config['llm']['model']).get()
        chain = build_llm_chain(
            llm,
            CONTEXT_ONLY_PROMPT()
        )
        self.report.append({
            "config": self.config,
            "llm": self.config['llm']['model'],
            "prompt": CONTEXT_ONLY_PROMPT()
        })

        rag_reports = []
        rag_configurations = self.config['rag_configurations']
        for rag_configuration in rag_configurations:
            self.log.info(f"Building RAG data: {rag_configuration['name']}")
            builder = RagBuilder(rag_configuration, self.log)
            builder.build()

            self.log.info(f"Loading RAG stack: {rag_configuration['name']}")
            rag_stack = self.getRagStack(rag_configuration, self.log)
            print("Stack Loaded")

            self.log.info(f"Running queries RAG stack: {rag_configuration['name']}")
            question_responses = []
            for test_query in self.config['test_queries']:
                response = rag_stack.query(
                    test_query['query'],
                    chain,
                    self.config['llm']['model']
                )
                if response == "":
                    response = "No response"
                    response_failed = True
                else:
                    if test_query['expected'] in response:
                        response_failed = False
                    else:
                        response_failed = True

                question_responses.append({
                    "query": test_query['query'],
                    "response": response,
                    "failed": response_failed
                })
            rag_reports.append({
                "config": rag_configuration,
                "responses": question_responses
            })

        self.writeReport()
        self.log.info("Tests complete.")

    def writeReport(self):
        self.log.info("Writing report...")
        with open(self.config['report'], 'w') as f:
            f.write(yaml.dump(self.report))

    def getRagStack(self, config, log):
        c = __import__(
            'core.' + config['stack']['class'],
            fromlist=['']
        )
        rs = getattr(c, config['stack']['class'])
        return rs(config, log)
