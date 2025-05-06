# This module will contain QA-related services extracted from the API routes.
from deckard.core.logger import Logger
from deckard.core.config import get_rag_pipelines

from deckard.core.config import get_api_llm_config
from deckard.core.time import cur_timestamp, time_since

def build_qa_stacks(log: Logger) -> dict:
    """Builds the QA stacks from the configuration.

    Args:
        log (Logger): The logger for the QA stacks.

    Returns:
        dict: The QA stacks.
    """
    stacks = {}
    log.info("Building QA Stacks...")
    pipelines = get_rag_pipelines()
    for w in pipelines.values():
        c = __import__(
            w['rag']['qa']['stack']['module_name'],
            fromlist=['']
        )
        qas = getattr(c, w['rag']['qa']['stack']['class_name'])
        stacks[w['name']] = qas(w['rag']['qa'], log)
    return stacks

def query_qa_stack(qa_stack, query_value, chains, timings):
    """
    Queries the QA stack and returns the response and metadata.

    Args:
        qa_stack: The QA stack to query.
        query_value: The query string.
        chains: The chains dictionary.
        timings: The dictionary to update timing values.

    Returns:
        tuple: (qa_response, source_urls)
    """
    logger = timings.get('logger')
    if logger:
        logger.info("Searching QA Stack...")

    qa_search_start = cur_timestamp()
    qa_response = qa_stack.query(query_value, chains['qa'], get_api_llm_config())
    timings['qa_search_time'] = time_since(qa_search_start)

    source_urls = []
    if 'links' in qa_response:
        for link in qa_response['links']:
            if 'url' in link:
                source_urls.append(link['url'])

    return qa_response, source_urls