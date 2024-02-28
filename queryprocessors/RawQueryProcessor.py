class RawQueryProcessor:
    def __init__(self, log):
        self.log = log

    def setQuery(self, query):
        self.query = query

    def getEmbeddingSearchQuery(self):
        return self.query

    def getOriginalQuery(self):
        return self.query
