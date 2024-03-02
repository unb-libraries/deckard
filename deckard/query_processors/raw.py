"""Provides the RawQueryProcessor class."""
from logging import Logger

class RawQueryProcessor:
    """Provides a class that alters user queries for embedding searches.

    Args:
        log (Logger): The logger.

    Attributes:
        log (Logger): The logger.
        query (str): The query.
    """
    def __init__(self, log: Logger) -> None:
        self.log = log
        self.query = ''

    def set_query(self, query: str) -> None:
        """Sets the query to process.

        Args:
            query (str): The query.
        """
        self.query = query

    def get_embedding_search_query(self) -> str:
        """Returns the query for the embedding search.

        Returns:
            str: The query.
        """
        return self.query

    def get_original_query(self) -> str:
        """Returns the original query.

        Returns:
            str: The original query.
        """
        return self.query
