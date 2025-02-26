import hashlib
import html2text
import json
import os
import requests
import time

from bs4 import BeautifulSoup
from logging import Logger
from pathlib import Path
from typing import TypeVar

from deckard.core import json_dumper
from deckard.core.utils import open_file_read

T = TypeVar('T', str, object)

class WebPageCollector:
    """Collects web pages. This is a base class.

    Args:
        config (dict): The configuration for the collector.
        log (Logger): The logger for the collector.

    Attributes:
        CACHE_PATH (str): The path to the cache directory.
        IGNORE_PAGE_STRINGS (list): The strings to ignore in the page.
        REQUEST_HEADERS (dict): The headers to use for requests.
        URL_LIST_FILE_PATHS (str): The path to the list of URLs to collect.
        config (dict): The configuration for the collector.
        log (Logger): The logger for the collector.
        page_queue (list): The queue of pages to collect.
        page_queue_index (int): The index of the current page in the queue.
    """

    CACHE_PATH = '/tmp'
    IGNORE_PAGE_STRINGS = [
        '404 This page is not available',
        '404 Page not found'
    ]
    REQUEST_HEADERS = {
        'User-Agent': 'Deckard/0.1 Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            + 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 '
            + 'Safari/537.3'
    }
    URL_LIST_FILE_PATHS = 'collectors/libpages/urls.txt'

    def __init__(self, config: dict, log: Logger) -> None:
        self.config = config
        self.log = log
        self.page_queue = []
        self.page_queue_index = 0
        self.cur_url = ''
        self.cur_content = ''
        if self.URL_LIST_FILE_PATHS:
            self._validate_data_paths()
            for url_file_path in self.URL_LIST_FILE_PATHS:
                self._queue_urls(url_file_path)

    def __iter__(self) -> None:
        return self

    def __next__(self) -> None:
        if self.page_queue_index < len(self.page_queue):
            url = self.page_queue[self.page_queue_index].strip()
            self.page_queue_index += 1
            return self._get_page_contents(url)
        raise StopIteration

    @staticmethod
    def name() -> str:
        """Retrieves the name of the collector.

        Returns:
            str: The name of the collector.
        """
        return 'Generic Web Page Collector'

    def _validate_data_paths(self) -> None:
        """Validates and creates the data paths."""
        if not os.path.exists(self.CACHE_PATH):
            os.makedirs(self.CACHE_PATH)

    def _queue_urls(self, url_file_path) -> None:
        """Queues the URLs to collect."""
        url_file = open_file_read(url_file_path)
        if not url_file:
            self.log.error("Failed to open file: %s", url_file_path)
            return
        # Iterate over the lines in the file and remove any that are empty or not a properly formatted URL
        validated_urls = []
        for line in url_file.readlines():
            line = line.strip()
            if not line:
                continue
            if not line.startswith('http'):
                continue
            validated_urls.append(line)
        self.page_queue.extend(validated_urls)

    def len(self) -> int:
        """Retrieves the length of the page queue.

        Returns:
            int: The length of the page queue.
        """
        return len(self.page_queue)

    def _get_page_contents(self, url) -> T:
        """Gets the page content and metadata.

        Args:
            url (str): The URL of the page to get.

        Returns:
            T: The page content and metadata.
        """
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
        if (
            not self.config['cache_urls']
            or not output_file.is_file()
            or not metadata_file.is_file()
        ):
            self.log.info("Downloading: %s", url)
            response = requests.get(
                url,
                headers=self.REQUEST_HEADERS,
                timeout=10
            )
            if not response.ok:
                self.log.warning("Failed to download: %s", url)
                return None, None
            response.encoding = response.apparent_encoding
            text = response.text
            output_file.write_text(text, encoding="utf-8")
            self.cur_url = url
            self.cur_content = response.content
            metadata_file.write_text(
                self._generate_metadata(),
                encoding="utf-8"
            )

        else:
            self.log.info("Using Locally Cached Data for: %s", url)
        return self._extract_page_text(
                output_file.read_text(encoding="utf-8")
            ), json.loads(metadata_file.read_text(encoding="utf-8"))

    def _generate_metadata(self) -> dict:
        """Generates the metadata for the page.

        Returns:
            dict: The metadata for the page.
        """
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

    def _extract_page_text(self, page_content) -> str:
        """Extracts the text from the page.

        Args:
            page_content (str): The content of the page.

        Returns:
            str: The text extracted from the page.
        """
        h = html2text.HTML2Text()
        h.ignore_links = self.config['ignore_links']
        h.images_to_alt = self.config['images_to_alt']
        h.unicode_snob = self.config['unicode_snob']

        text = h.handle(
            self._strip_page_cruft(page_content)
        )
        text = text.replace('#', '-')
        return text

    @staticmethod
    def _strip_page_cruft(page_content) -> str:
        """Strips the cruft from the page.

        Args:
            page_content (str): The content of the page.

        Returns:
            str: The content of the page with the cruft stripped.
        """
        body_split = page_content.split('<body>')
        if len(body_split) > 1:
            return body_split.split('</body>')[0]
        else:
            return page_content

    def ignore_item(self, page_content) -> bool:
        """Determines if the page should be ignored.

        Args:
            page_content (str): The content of the page.

        Returns:
            bool: True if the page should be ignored, False otherwise.
        """
        for ignore_string in self.IGNORE_PAGE_STRINGS:
            if ignore_string in page_content:
                return True
        return False
