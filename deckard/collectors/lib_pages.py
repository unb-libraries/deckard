import os

from deckard.core import get_data_dir

from .webpages import WebPageCollector

class LibPagesCollector(WebPageCollector):
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
        return 'UNB Libraries Webpage Collector'

    @staticmethod
    def stripPageCruft(page_content: str) -> str:
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
