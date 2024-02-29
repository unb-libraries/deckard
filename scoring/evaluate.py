import yaml

from core.logger import get_logger
from scoring.RagTester import RagTester

def start():
    log = get_logger()
    log.info("Starting...")

    config = yaml.safe_load(open("scoring/config.yml"))
    tests = RagTester(
        log,
        config['evaluate']
    )
    tests.run()
