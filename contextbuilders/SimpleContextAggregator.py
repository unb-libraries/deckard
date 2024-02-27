class SimpleContextAggregator:
    def __init__(self, log):
        self.log = log

    def buildContext(self, results, database, context_size):
        self.results = results
        context = ""
        for ind in results.index:
            item = results['text'][ind]
            context += item + "\n"
            if len(context) >= context_size:
                break
        return context[:context_size]
