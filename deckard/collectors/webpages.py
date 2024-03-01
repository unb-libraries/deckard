import hashlib
import html2text
import json
import os
import requests
import time

from bs4 import BeautifulSoup
from logging import Logger
from pathlib import Path

from deckard.core import json_dumper

class WebPageCollector:
    CACHE_PATH = '/tmp'
    IGNORE_PAGE_STRINGS = [
        '404 This page is not available',
        '404 Page not found'
    ]
    REQUEST_HEADERS = {
        'User-Agent': 'Deckard/0.1 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    }
    URL_LIST_FILE_PATH = 'collectors/libpages/urls.txt'

    def __init__(self, config: dict, log: Logger) -> None:
        self.config = config
        self.page_queue = []
        self.page_queue_index = 0
        if self.URL_LIST_FILE_PATH:
            self.validateDataPaths()
            self.queueUrls()
            self.log = log

    def __iter__(self):
        return self

    def __next__(self):
        if self.page_queue_index < len(self.page_queue):
            url = self.page_queue[self.page_queue_index].strip()
            self.page_queue_index += 1
            return self.getPage(url)
        else:
            raise StopIteration

    @staticmethod
    def name():
        return 'Generic Web Page Collector'

    def validateDataPaths(self):
        if not os.path.exists(self.CACHE_PATH):
            os.makedirs(self.CACHE_PATH)

    def queueUrls(self):
        url_file = open(self.URL_LIST_FILE_PATH , 'r')
        self.page_queue = url_file.readlines()

    def len(self):
        return len(self.page_queue)

    def getPage(self, url):
        hash_rep = hashlib.md5(url.encode('utf-8')).hexdigest()
        output_filename = os.path.join(
            self.CACHE_PATH,
            hash_rep
        ) + '.html'
        metadata_filename = os.path.join(
            self.CACHE_PATH,
            hash_rep
        ) + '.json'
        output_file = Path(output_filename)
        metadata_file = Path(metadata_filename)
        if not self.config['cache_urls'] or not output_file.is_file() or not metadata_file.is_file():
            self.log.info("Downloading: " + url)
            response = requests.get(
                url,
                headers=self.REQUEST_HEADERS
            )
            if not response.ok:
                self.log.warning("Failed to download: " + url)
                return None, None
            response.encoding = response.apparent_encoding
            text = response.text
            output_file.write_text(text)
            self.cur_url = url
            self.cur_content = response.content
            metadata_file.write_text(self.generate_metadata())

        else:
            self.log.info("Using Locally Cached Data for: " + url)
        return self.extractPageText(
            output_file.read_text()
        ), json.loads(metadata_file.read_text())

    def generate_metadata(self):
        soup = BeautifulSoup(self.cur_content, features="html.parser")

        title = soup.find("meta", property="og:title")
        if not title:
            title_string = soup.title.string
        else:
            title_string = title["content"]

        metadata = {
            "title": title_string,
            "collector": self.name(),
            "source_type": "webpage",
            "timestamp": time.time(),
            "source": self.cur_url
        }
        return json_dumper(metadata)

    def extractPageText(self, page_content):
        h = html2text.HTML2Text()
        h.ignore_links = self.config['ignore_links']
        h.images_to_alt = self.config['images_to_alt']
        h.unicode_snob = self.config['unicode_snob']

        text = h.handle(
            self.stripPageCruft(page_content)
        )
        text = text.replace('#', '-')
        return text

    @staticmethod
    def stripPageCruft(page_content):
        body_split = page_content.split('<body>')
        if len(body_split) > 1:
            return body_split.split('</body>')[0]
        else:
            return page_content

    def ignoreItem(self, page_content):
        for ignore_string in self.IGNORE_PAGE_STRINGS:
            if ignore_string in page_content:
                return True
        return False
