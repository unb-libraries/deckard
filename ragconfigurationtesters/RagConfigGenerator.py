
import itertools
import re
import sys
import yaml

from logging import Logger

class RagConfigGenerator:
    MAX_TEST_RUNS = 256

    def __init__(
        self,
        filepath: str,
        log: Logger
    ) -> None:
        self.config_index = 0
        self.configurations = []
        config_file_spintax  = open(filepath, 'r').read()
        for config in self.spintax(config_file_spintax):
            self.configurations.append(
                yaml.safe_load(config)
            )
        log.info(f"Loaded {len(self.configurations)} configurations")
        if len(self.configurations) > self.MAX_TEST_RUNS:
            log.error(f"Cowardly refusing to process more than {self.MAX_TEST_RUNS} configurations.")
            sys.exit(1)

    def __iter__(self) -> None:
        return self

    def __next__(self) -> None:
        if self.config_index < len(self.configurations):
            config = self.configurations[self.config_index]
            self.config_index += 1
            return config
        else:
            raise StopIteration

    def spintax(self, text:str) -> list:
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