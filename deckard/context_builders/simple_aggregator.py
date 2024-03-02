"""Provides the SimpleContextAggregator class."""
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

    def build_context(self, results, database, context_size):
        """Builds the context from the results.

        Args:
            results (Dataframe): The results to build the context from.
            database (ContextDatabase): The context database to build the context from.
            context_size (int): The size of the context to build.

        Returns:
            T: The context and the metadata.
        """
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
