import os

from deckard.core import get_data_dir
from .webpages import WebPageCollector

class LibPagesCollector(WebPageCollector):
    """Collects webpages from the UNB Libraries website.

    Args:
        config (dict): The configuration for the collector.
        log (Logger): The logger for the collector.

    Attributes:
        CACHE_PATH (str): The path to the cache directory.
        IGNORE_PAGE_STRINGS (list): The strings to ignore in the page.
        URL_LIST_FILE_PATH (str): The path to the list of URLs to collect.

    .. data:: OUTPUT_PATH
        The path to write the chunks to.
    """
    CACHE_PATH = os.path.join(
        get_data_dir(),
        'collectors',
        'libpages',
        'cache'
    )
    IGNORE_PAGE_STRINGS = [
        '404 Page Not Found'
    ]
    URL_LIST_FILE_PATH = 'deckard/collectors/data/lib_urls.txt'

    @staticmethod
    def name() -> str:
        """Retrieves the name of the collector.

        Returns:
            str: The name of the collector.
        """
        return 'UNB Libraries Webpage Collector'

    @staticmethod
    def _strip_page_cruft(page_content: str) -> str:
        """Strips cruft from the page content.

        Args:
            page_content (str): The content of the page.

        Returns:
            str: The stripped content of the page.
        """
        page_test = page_content.split('block-pagetitle')
        if len(page_test) < 2:
            page_test = page_content.split('block-mainpagecontent')
            if len(page_test) < 2:
                page_content = page_content.split('div id="main"')[1]
            else:
                page_content = page_content.split('block-mainpagecontent')[1]
                page_content = page_content.split('<div class="content">', 1)[1]
        else:
            page_content = page_content.split('block-pagetitle')[1]
            page_content = page_content.split('<div class="content">', 1)[1]
        page_content = page_content.split('<footer class="site-footer')[0]
        return page_content
