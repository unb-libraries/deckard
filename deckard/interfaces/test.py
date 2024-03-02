"""Tests components without bootstrapping the entire application."""
from deckard.core import get_logger
from deckard.core.config import get_api_llm_config
from deckard.llm import LLM

DECKARD_CMD_STRING = 'test'

def run():
    log = get_logger()
    log.info("Loading LLM...")
    config = get_api_llm_config()
    print(config)
    llm = LLM(log, get_api_llm_config()).get()
    # llm = LLM(log, get_api_llm_config()).get()
    # app.config['llm'] = llm
