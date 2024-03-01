class SimpleContextAggregator:
    def __init__(self, log):
        self.log = log

    def buildContext(self, results, database, context_size):
        self.results = results
        metadata = {'contextbuilder' : {'chunks_used': [], 'context': '', 'context_length': 0}}

        context = ""
        for ind in results.index:
            item = results['text'][ind]
            context += item + "\n"
            metadata['contextbuilder']['chunks_used'].append(results['text'][ind])
            if len(context) >= context_size:
                break
        final_context = context[:context_size]
        metadata['contextbuilder']['context'] = final_context
        metadata['contextbuilder']['context_length'] = len(final_context)
        return final_context, metadata
