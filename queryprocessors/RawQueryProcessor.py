class RawQueryProcessor:
    def __init__(self, query, log):
        self.log = log
        self.query = query

    def getEmbeddingSearchQuery(self):
        return self.query

    def getOriginalQuery(self):
        return self.query
