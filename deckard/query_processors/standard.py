from .raw import RawQueryProcessor

class StandardQueryProcessor(RawQueryProcessor):
    """Provides a class that alters user queries for embedding searches.

    Args:
        log (Logger): The logger.

    Attributes:
        PREFIXES (list): The prefixes to remove from the query.
        log (Logger): The logger.
        query (str): The query.
    """

    PREFIXES = [
        'who are the',
        'what are the',
        'where are the',
        'who is the',
        'what is the',
        'where is the',
        'who is',
        'what is',
        'where is',
        'who are',
        'what are',
        'where are',
        'who',
        'what',
        'where',
    ]

    def get_embedding_search_query(self) -> str:
        """Returns the query for the embedding search.

        Returns:
            str: The query.
        """
        lower_query = self.query.lower()
        for prefix in self.PREFIXES:
            if lower_query.startswith(prefix.lower()):
                self.log.info("Removing Query Prefix: %s", prefix)
                return self._strip_trailing_punctuation(
                    self.query[len(prefix):]
                ).strip()
        return self._strip_trailing_punctuation(self.query).strip()

    def _strip_trailing_punctuation(self, query: str) -> str:
        """Strips trailing punctuation from the query.

        Args:
            query (str): The query.

        Returns:
            str: The query without trailing punctuation.
        """
        return query.rstrip('.,?!')
