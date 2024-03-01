from logging import Logger

class RawQueryProcessor:
    def __init__(self, log: Logger) -> None:
        self.log = log

    def setQuery(self, query: str) -> None:
        self.query = query

    def getEmbeddingSearchQuery(self) -> str:
        return self.query

    def getOriginalQuery(self) -> str:
        return self.query
