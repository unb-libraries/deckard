from typing import TypeVar

T = TypeVar('T', str, dict)

class SimpleContextAggregator:
    """Aggregates the context from the results.

    Args:
        log (Logger): The logger for the context builder.
    """

    def __init__(self, log):
        self.results = None
        self.log = log

    def build_context(self, dense_results, sparse_results, database, context_size):
        """Builds the context from the results.

        Args:
            dense_results (Dataframe): The results to build the context from.
            sparse_results (Dataframe): The results to build the context from.
            database (ContextDatabase): The context database to build the context from.
            context_size (int): The size of the context to build.

        Returns:
            T: The context and the metadata.
        """
        results = []

        dense_iter = iter(dense_results['text'].items())
        sparse_iter = iter(sparse_results)

        # Zip the items together ranked by score.
        while True:
            try:
                dense_item = next(dense_iter)
                results.append(dense_item[1])
            except StopIteration:
                break

            try:
                sparse_item = next(sparse_iter)
                results.append(sparse_item['document'][0])
            except StopIteration:
                break

        self.results = results
        metadata = {'contextbuilder' : {'chunks_used': [], 'context': '', 'context_length': 0}}

        context = ""
        for result in results:
            item = result
            context += item + "\n"
            metadata['contextbuilder']['chunks_used'].append(result)
            if len(context) >= context_size:
                break
        final_context = context[:context_size]
        metadata['contextbuilder']['context'] = final_context
        metadata['contextbuilder']['context_length'] = len(final_context)
        return final_context, metadata
