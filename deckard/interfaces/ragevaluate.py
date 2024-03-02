"""Provides a command to evaluate RAG pipelines."""
from deckard.core import get_logger
from deckard.rag_evaluator import RagPipelineEvaluator
from deckard.core.yaml import load_yaml

DECKARD_CMD_STRING = 'evaluate:rag'

def start() -> None:
    """Starts the RAG pipeline evaluator."""
    log = get_logger()
    log.info("Loading Configuration...")
    config = load_yaml("deckard/rag_evaluator/config.yml")

    for test in config['ragconfigurationtests']:
        log.info("Running test: %s", test['name'])
        tests = RagPipelineEvaluator(
            log,
            test
        )
        tests.run()
