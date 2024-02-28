import yaml

from core.logger import get_logger

def start():
    log = get_logger()
    log.info("Starting...")

    tests = RagTester(
        log,
        yaml.safe_load(open("config.yml"))
    )
    tests.run()

class RagTester:
    def __init__(self, log, config):
        self.log = log

    def run(self):
        self.log.info("Running tests...")

        self.log.info("Tests complete.")
