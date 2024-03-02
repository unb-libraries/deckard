from logging import Logger
import os

import dictdiffer
from box import Box
from pandas import DataFrame

from deckard.core import get_data_dir
from deckard.core import json_dumper
from deckard.core.time import cur_timestamp, time_since
from deckard.core.utils import gen_uuid

class RagEvaluatorReporter:
    REPORT_PATH = os.path.join(
        get_data_dir(),
        'reports',
        'ragconfigtests'
    )

    def __init__(
        self,
        config: dict,
        log: Logger,
        start: float
    ) -> None:
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
    def addConfiguration(
        self,
        id: str,
        config: dict,
        score: float
    ) -> None:
        self.configurations[id] = {
            'configuration': config,
            'score': score
        }

    def addScoreboardItem(
        self,
        id: str,
        name: str,
        score: float
    ) -> None:
        self.scoreboard.loc[len(self.scoreboard.index)] = [id, name, score]

    def addSummaryItem(
        self,
        id: str,
        name: str,
        score: float,
        data: dict,
        average_response_time: float
    ) -> None:
        self.summaries.loc[len(self.summaries.index)] = [id, name, score, data, average_response_time]

    def addDetailItem(
        self,
        id: str,
        name: str,
        score: float,
        data: dict
    ) -> None:
        self.details.loc[len(self.details.index)] = [id, name, score, data]

    def writeReport(self) -> None:
        self.log.info("Analyzing Configuration Changes...")
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
            f"{cur_timestamp()}_{self.id}.json"
        )
        with open(output_file, 'w') as f:
            f.write(
                json_dumper(
                    final_report
                )
            )

    def analyzeConfigurations(self) -> None:
        self.log.info("Analyzing configurations...")
        self.analysis = {}
        all_configs = []
        for config in self.configurations.values():
            all_configs.append(config['configuration'])
        unique_items_in_config = self.uniqueDictItems(all_configs)
        raw_params = self.getUniqueItemScores(all_configs, unique_items_in_config)
        sorted_params = {}
        for param, values in raw_params.items():
            sorted_params[param] = dict(sorted(values.items(), key=lambda item: item[1]['average_score'], reverse=True))
        self.param_analysis = sorted_params

        self.sb = self.scoreboard.sort_values(by=["score"], ascending=False).to_dict(orient='records')
        for idx, sb_config in enumerate(self.sb):
            self.sb[idx]['values'] = self.getDictsUniqueItems(self.getConfigFromId(sb_config['id']), unique_items_in_config)
        self.sb.sort(key=lambda x: x['score'], reverse=True)

    def getConfigFromId(self, id: str) -> dict:
        for config_id, config_test in self.configurations.items():
            if config_id == id:
                return config_test['configuration']
        return {}

    def getConfigScore(self, config: dict) -> float:
        for config_id, config_test in self.configurations.items():
            if config_test['configuration'] == config:
                return config_test['score']
        return 0

    def uniqueDictItems(self, dict_list: list) -> dict:
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

    def getDictsUniqueItems(
        self,
        dict: dict,
        unique_items: dict
    ) -> dict:
        dict_unique_items = {}
        dot_dict = Box(dict)
        for key in unique_items.keys():
            dict_unique_items[key] = eval(f"dot_dict.{key}")
        return dict_unique_items

    def getDictsItemValue(
        self,
        dict: dict,
        namespace: str
    ) -> str:
        dot_dict = Box(dict)
        return eval(f"dot_dict.{namespace}")

    def getUniqueItemScores(
        self,
        config_list: dict,
        unique_items: dict
    ) -> dict:
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
