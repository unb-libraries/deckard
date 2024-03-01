import yaml

from core.logger import get_logger
from ragconfigurationtesters.RagTester import RagTester

def start():
    log = get_logger()
    log.info("Loading Configuration...")
    config = yaml.safe_load(open("ragconfigurationtesters/config.yml"))

    for test in config['ragconfigurationtests']:
        log.info(f"Running test: {test['name']}")
        tests = RagTester(
            log,
            test
        )
        tests.run()
