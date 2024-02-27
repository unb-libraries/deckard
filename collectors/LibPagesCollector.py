import os

from collectors.WebPageCollector import WebPageCollector
from core.config import get_data_dir

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
    URL_LIST_FILE_PATH = 'collectors/data/lib_urls.txt'

    def name(self):
        return 'UNB Libraries Webpage Collector'

    def stripPageCruft(self, page_content):
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
