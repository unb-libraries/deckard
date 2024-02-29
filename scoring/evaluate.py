import dictdiffer
import itertools
import json
import re
import sys
import yaml

from core.builders import build_llm_chain
from core.LLM import LLM
from core.logger import get_logger
from core.prompts import CONTEXT_ONLY_PROMPT
from core.RagBuilder import RagBuilder
from pandas import DataFrame
from secrets import token_hex
from core.utils import clear_gpu_memory

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

    def run(self):
        self.log.info("Running tests...")
        self.log.info("Loading LLM...")
        rag_configs = RagConfigGenerator("scoring/" + self.config['input'], self.log)

        llm = LLM(self.log, self.config['llm']['model']).get()
        prompt = CONTEXT_ONLY_PROMPT()


        reporter = RagReporter(self.config, self.log)
        for rag_configuration in rag_configs:
            chain = build_llm_chain(
                llm,
                prompt
            )

            configuration_id = token_hex(32)
            score = 0
            self.log.info(f"Building RAG data: {rag_configuration['name']}")
            builder = RagBuilder(rag_configuration, self.log)
            builder.build()

            self.log.info(f"Loading RAG stack: {rag_configuration['name']}")
            rag_stack = self.getRagStack(rag_configuration, self.log)

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
                        score += 1
                        response_failed = False
                    else:
                        response_failed = True

                question_responses.append({
                    "query": test_query['query'],
                    "expected": test_query['expected'],
                    "response": response,
                    "failed": response_failed
                })
            reporter.addScoreboardItem(
                configuration_id,
                rag_configuration['name'],
                score
            )
            reporter.addSummaryItem(
                configuration_id,
                rag_configuration['name'],
                score,
                question_responses
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

            # Clean up
            del(builder)
            del(rag_stack)
            del(chain)
            clear_gpu_memory()

        reporter.writeReport()
        self.log.info("Tests complete.")

    def getRagStack(self, config, log):
        c = __import__(
            'core.' + config['stack']['class'],
            fromlist=['']
        )
        rs = getattr(c, config['stack']['class'])
        return rs(config, log)


class RagReporter:
    def __init__(self, config, log):
        self.log = log
        self.config = config
        self.configurations = {}
        self.scoreboard = DataFrame(
            [],
            columns=['id', 'name', 'score']
        )
        self.summaries = DataFrame(
            [],
            columns=['id', 'name', 'score', 'data']
        )
        self.details = DataFrame(
            [],
            columns=['id', 'name', 'score', 'data']
        )
    def addConfiguration(self, id, config, score):
        self.configurations[id] = {
            'configuration': config,
            'score': score
        }

    def addScoreboardItem(self, id, name, score):
        self.scoreboard.loc[len(self.scoreboard.index)] = [id, name, score]

    def addSummaryItem(self, id, name, score, data):
        self.summaries.loc[len(self.summaries.index)] = [id, name, score, data]

    def addDetailItem(self, id, name, score, data):
        self.details.loc[len(self.details.index)] = [id, name, score, data]

    def writeReport(self):
        self.log.info("Analyzing Configurations Changes...")
        self.analyzeConfigurations()
        self.log.info("Writing report...")
        final_report = {
            "scoreboard": self.scoreboard.sort_values(by=["score"], ascending=False).to_dict(orient='records'),
            "parameters": self.param_analysis,
            "summaries": self.summaries.sort_values(by=["score"], ascending=False).to_dict(orient='records'),
            "details": self.details.sort_values(by=["score"], ascending=False).to_dict(orient='records'),
            "configurations": self.configurations,
            "analysis": self.analysis
        }
        with open(self.config['report'], 'w') as f:
            f.write(json.dumps(final_report, indent=4))

    def analyzeConfigurations(self):
        self.log.info("Analyzing configurations...")
        self.analysis = {}
        variance_scores = {}
        last_config = None
        add_previous = True
        for config in self.configurations.values():
            if not last_config is None:
                for diff in list(dictdiffer.diff(config['configuration'], last_config['configuration'])):
                    config_element = diff[1]
                    if not config_element in variance_scores.keys():
                        variance_scores[config_element] = {}

                    config_value = list(diff[2])[1]
                    if not config_value in variance_scores[config_element].keys():
                        variance_scores[config_element][config_value] = {
                            "avg_score": 0,
                            "scores": [],
                        }
                    variance_scores[config_element][config_value]["scores"].append(config['score'])
                    variance_scores[config_element][config_value]["avg_score"] = sum(variance_scores[config_element][config_value]["scores"]) / len(variance_scores[config_element][config_value]["scores"])

                    if add_previous:
                        config_value = list(diff[2])[0]
                        if not config_value in variance_scores[config_element].keys():
                            variance_scores[config_element][config_value] = {
                                "avg_score": 0,
                                "scores": [],
                            }
                        variance_scores[config_element][config_value]["scores"].append(last_config['score'])
                        variance_scores[config_element][config_value]["avg_score"] = sum(variance_scores[config_element][config_value]["scores"]) / len(variance_scores[config_element][config_value]["scores"])
                        add_previous = False
            last_config = config
        self.param_analysis = variance_scores

class RagConfigGenerator:
    def __init__(self, filepath, log):
        self.config_index = 0
        self.configurations = []
        config_file_spintax  = open(filepath, 'r').read()
        for config in spintax(config_file_spintax, False):
            self.configurations.append(
                yaml.safe_load(config)
            )
        log.info(f"Loaded {len(self.configurations)} configurations")
        if len(self.configurations) > 128:
            log.error("Cowardly refusing to process more than 128 configurations.")
            sys.exit(1)

    def __iter__(self):
        return self

    def __next__(self):
        if self.config_index < len(self.configurations):
            config = self.configurations[self.config_index]
            self.config_index += 1
            return config
        else:
            raise StopIteration

def spintax(text, single=True):
    pattern = re.compile(r'(\{[^\}]+\}|[^\{\}]*)')
    chunks = pattern.split(text)

    def options(s):
        if len(s) > 0 and s[0] == '{':
            return [opt for opt in s[1:-1].split('|')]
        return [s]

    parts_list = [options(chunk) for chunk in chunks]

    spins = []

    for spin in itertools.product(*parts_list):
        spins.append(''.join(spin))
    return spins
