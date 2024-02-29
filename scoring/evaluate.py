import time
import dictdiffer
import itertools
import json
import re
import sys
import yaml

from box import Box
from core.builders import build_llm_chain
from core.LLM import LLM
from core.logger import get_logger
from core.prompts import CONTEXT_ONLY_PROMPT
from core.RagBuilder import RagBuilder
from pandas import DataFrame
from secrets import token_hex
from core.utils import clear_gpu_memory

"""
@SEE: https://media.licdn.com/dms/image/D5622AQGdlqVl8KSfwA/feedshare-shrink_800/0/1685131406579?e=1712188800&v=beta&t=avMJcbC-GOniaM-ziLAdYDJrzy3ZuuF7my2YfgoOqv4
"""
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

            # Clean up
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
            columns=['id', 'name', 'score', 'data', 'average_response_time']
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

    def addSummaryItem(self, id, name, score, data, average_response_time):
        self.summaries.loc[len(self.summaries.index)] = [id, name, score, data, average_response_time]

    def addDetailItem(self, id, name, score, data):
        self.details.loc[len(self.details.index)] = [id, name, score, data]

    def writeReport(self):
        self.log.info("Analyzing Configurations Changes...")
        self.analyzeConfigurations()
        self.log.info("Writing report...")
        final_report = {
            "scoreboard": self.sb,
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
        all_configs = []
        for config in self.configurations.values():
            all_configs.append(config['configuration'])
        unique_items_in_config = self.uniqueDictItems(all_configs)
        self.param_analysis = self.getUniqueItemScores(all_configs, unique_items_in_config)
        self.sb = self.scoreboard.sort_values(by=["score"], ascending=False).to_dict(orient='records')
        for idx, sb_config in enumerate(self.sb):
            self.sb[idx]['values'] = self.getDictsUniqueItems(self.getConfigFromId(sb_config['id']), unique_items_in_config)
        self.sb.sort(key=lambda x: x['score'], reverse=True)

    def getConfigFromId(self, id):
        for config_id, config_test in self.configurations.items():
            if config_id == id:
                return config_test['configuration']
        return {}

    def getConfigScore(self, config):
        for config_id, config_test in self.configurations.items():
            if config_test['configuration'] == config:
                return config_test['score']
        return 0

    def uniqueDictItems(self, dict_list):
        different_elements = {}
        for dictionary in dict_list:
            for dictionary_comp in dict_list:
                for diff in list(dictdiffer.diff(dictionary, dictionary_comp)):
                    for value in diff[2]:
                        if not diff[1] in different_elements.keys():
                            different_elements[diff[1]] = []
                        if not value in different_elements[diff[1]]:
                            different_elements[diff[1]].append(value)
        return different_elements

    def getDictsUniqueItems(self, dict, unique_items):
        dict_unique_items = {}
        dot_dict = Box(dict)
        for key in unique_items.keys():
            dict_unique_items[key] = eval(f"dot_dict.{key}")
        return dict_unique_items

    def getDictsItemValue(self, dict, namespace):
        dot_dict = Box(dict)
        return eval(f"dot_dict.{namespace}")

    def getUniqueItemScores(self, config_list, unique_items):
        unique_item_scores = {}
        for unique_item_ns, unique_values in unique_items.items():
            if unique_item_ns not in unique_item_scores:
                unique_item_scores[unique_item_ns] = {}
            for unique_value in unique_values:
                if unique_value not in unique_item_scores[unique_item_ns]:
                    unique_item_scores[unique_item_ns][unique_value] = {
                        "average_score": 0,
                        "scores": []
                    }
                for config in config_list:
                    if self.getDictsItemValue(config, unique_item_ns) == unique_value:
                        unique_item_scores[unique_item_ns][unique_value]['scores'].append(self.getConfigScore(config))
                        unique_item_scores[unique_item_ns][unique_value]['average_score'] = sum(unique_item_scores[unique_item_ns][unique_value]['scores']) / len(unique_item_scores[unique_item_ns][unique_value]['scores'])
        return unique_item_scores

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
