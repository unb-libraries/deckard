"""Tests components without bootstrapping the entire application."""

from deckard.collectors import ArchivesHistoryCollector
from deckard.core import get_logger
from deckard.core.utils import replace_html_tables_with_csv, open_file_read

DECKARD_CMD_STRING = 'test'

def run():
    file = open_file_read('test.html')
    text = file.read()
    file.close()
    text = replace_html_tables_with_csv(text)
    print(text)
