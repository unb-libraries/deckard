# This module will contain QA-related services extracted from the API routes.

from deckard.core.config import get_api_llm_config
from deckard.core.time import cur_timestamp, time_since

def query_qa_stack(qa_stack, query_value, chains, logger):
    """
    Queries the QA stack and returns the response and metadata.

    Args:
        qa_stack: The QA stack to query.
        query_value: The query string.
        chains: The chains dictionary.
        logger: Logger instance.

    Returns:
        tuple: (qa_response, qa_search_time, source_urls)
    """
    logger.info("Searching QA Stack...")
    qa_search_start = cur_timestamp()
    qa_response = qa_stack.query(query_value, chains['qa'], get_api_llm_config())
    qa_search_time = time_since(qa_search_start)

    source_urls = []
    if 'links' in qa_response:
        for link in qa_response['links']:
            if 'url' in link:
                source_urls.append(link['url'])

    return qa_response, qa_search_time, source_urls