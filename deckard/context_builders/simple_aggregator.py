import pandas as pd
from typing import TypeVar

T = TypeVar('T', str, dict)

class SimpleContextAggregator:
    """Aggregates the context from the results.

    Args:
        log (Logger): The logger for the context builder.
    """

    def __init__(self, log):
        self.results = []
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
        # Rename dataframe columns to a common schema
        dense_results = dense_results.rename(columns={'text': 'value'})
        sparse_results = sparse_results.rename(columns={'document': 'value'})

        # Reset indices for interleaving
        dense_results = dense_results.reset_index(drop=True)
        sparse_results = sparse_results.reset_index(drop=True)

        # Concatenate and sort to interleave
        combined_results = pd.concat([dense_results, sparse_results], keys=['dense_results', 'sparse_results']).sort_index(level=1)

        metadata = {'contextbuilder' : {'chunks_used': [], 'context': '', 'context_length': 0}}
        context = ""
        for chunk in combined_results.iterrows():
            row_text = chunk[1]['value']
            context += row_text + "\n"
            chunk_metadata = chunk[1]['metadata']
            metadata['contextbuilder']['chunks_used'].append(
                {
                    'chunk': row_text,
                    'metadata': chunk_metadata
                }
            )
            if len(context) >= context_size:
                break

        final_context = context[:context_size]
        metadata['contextbuilder']['context'] = final_context
        metadata['contextbuilder']['context_length'] = len(final_context)

        return final_context, metadata
