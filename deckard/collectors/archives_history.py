import html2text
import mysql.connector
import os

from logging import Logger
from markdown_plain_text.extention import convert_to_plain_text

from deckard.core.utils import replace_html_tables_with_csv

from .mysql import MySQLCollector

class ArchivesHistoryCollector(MySQLCollector):
    """Collects data from the UNB Archives Wiki History database.
    """

    SOURCE_SLUG = 'unbhistory'

    ITEM_QUERY_SQL = """
SELECT p.page_title as title, t.old_text as text
FROM page AS p
JOIN revision AS rev
ON p.page_latest = rev.rev_id
JOIN text AS t
ON rev.rev_page = t.old_id
"""

    MYSQL_DB_CONFIG = {
        'host': 'localhost',
        'port': '3306',
        'database': 'unbhistory'
    }

    def __init__(self, config: dict, log: Logger) -> None:
        super().__init__(config, log)

        config = self.MYSQL_DB_CONFIG
        config['user'] = os.environ['UNBHISTORY_USER']
        config['password'] = os.environ['UNBHISTORY_PASS']

        self.connection = mysql.connector.connect(**config)
        cursor = self.connection.cursor()
        cursor.execute(self.ITEM_QUERY_SQL)
        for (title, text) in cursor:
            title_str = title.decode('utf-8')
            text_str = text.decode('utf-8')
            if not text_str == 'Importing file':
                self._write_cache_file(text_str, title_str)
                self.item_queue.append(
                    {
                        'title': title_str,
                        'text': text_str
                    }
                )
        cursor.close()

    def name(self) -> str:
        return 'UNB Archives Wiki History Collector'

    def _process_item(self, item: dict) -> str:
        html = item['text']
        html = replace_html_tables_with_csv(html)
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.images_to_alt = True
        h.unicode_snob = True
        return_text = h.handle(html)
        return_text = convert_to_plain_text(return_text)
        return_text = return_text.replace("'''", "")
        return_text = return_text.replace("''", "")
        return return_text, self._generate_metadata(item['title'])

    def ignore_item(self, content: str) -> bool:
        return False
