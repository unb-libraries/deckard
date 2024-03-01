from .raw import RawQueryProcessor

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

class StandardQueryProcessor(RawQueryProcessor):
    def getEmbeddingSearchQuery(self) -> str:
        lower_query = self.query.lower()
        for prefix in PREFIXES:
            if lower_query.startswith(prefix.lower()):
                self.log.info(f"Removing Query Prefix: {prefix}")
                return self.stripTrailingPunctuation(
                    self.query[len(prefix):]
                ).strip()
        return self.stripTrailingPunctuation(self.query).strip()

    def stripTrailingPunctuation(self, query: str) -> str:
        return query.rstrip('.,?!')
