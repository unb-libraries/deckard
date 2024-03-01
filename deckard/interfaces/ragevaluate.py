import yaml

from deckard.core import get_logger
from deckard.rag_evaluator import RagPipelineEvaluator

CMD_STRING = 'evaluate:rag'

def start() -> None:
    log = get_logger()
    log.info("Loading Configuration...")
    config = yaml.safe_load(open("deckard/rag_evaluator/config.yml"))

    for test in config['ragconfigurationtests']:
        log.info(f"Running test: {test['name']}")
        tests = RagPipelineEvaluator(
            log,
            test
        )
        tests.run()
