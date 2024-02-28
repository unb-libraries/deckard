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


        self.log.info("Tests complete.")

    def getRagStack(self, config, log):
        c = __import__(
            'core.' + config['stack']['class'],
            fromlist=['']
        )
        rs = getattr(c, config['stack']['class'])
        return rs(config['rag'], log)
