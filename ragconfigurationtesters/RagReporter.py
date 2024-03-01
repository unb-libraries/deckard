import dictdiffer
import os
import json

from box import Box
from core.config import get_data_dir
from core.time import cur_timestamp, time_since
from core.utils import gen_uuid
from pandas import DataFrame

class RagReporter:
    REPORT_PATH = os.path.join(
        get_data_dir(),
        'reports',
        'ragconfigtests'
    )

    def __init__(self, config, log, start):
        self.log = log
        self.name = config['name']
        self.id = gen_uuid()
        self.start = start
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
            "name": self.name,
            "length": time_since(self.start),
            "num_configurations": len(self.configurations),
            "scoreboard": self.sb,
            "parameters": self.param_analysis,
            "summaries": self.summaries.sort_values(by=["score"], ascending=False).to_dict(orient='records'),
            "details": self.details.sort_values(by=["score"], ascending=False).to_dict(orient='records'),
            "configurations": self.configurations,
            "analysis": self.analysis
        }
        if not os.path.exists(self.REPORT_PATH):
            os.makedirs(self.REPORT_PATH)
        output_file = os.path.join(
            self.REPORT_PATH,
            f"{self.id}_{cur_timestamp()}.json"
        )
        with open(output_file, 'w') as f:
            f.write(
                json.dumps(
                    final_report,
                    indent=4
                )
            )

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
