"""Provides the ParentDocumentAssembler class."""
from typing import TypeVar

from pandas import DataFrame as Dataframe

from deckard.databases.context_database import ContextDatabase
from .simple_aggregator import SimpleContextAggregator

T = TypeVar('T', str, dict)

class ParentDocumentAssembler(SimpleContextAggregator):
    """Assembles the parent document from the context database.

    Args:
        log (Logger): The logger for the context builder.
    """

    def build_context(
            self,
            results: Dataframe,
            database: ContextDatabase,
            context_size: int
        ) -> T:
        """Builds the context from the context database.

        Args:
            results (Dataframe): The results to build the context from.
            database (ContextDatabase): The context database to build the context from.
            context_size (int): The size of the context to build.

        Returns:
            T: The context and the metadata.
        """
        self.results = results
        context = ""
        metadata = {'contextbuilder' : {'documents_generated': [], 'context': '', 'context_length': 0}}
        for ind in results.index:
            sql = f"SELECT text, chunk_id FROM {database.CONTEXT_TABLE_NAME} WHERE doc_id = '{results['doc_id'][ind]}' ORDER BY chunk_id ASC"
            cursor = database.conn.execute(sql)
            doc_chunks = cursor.fetchall()
            document = ""

            # Reassemble the original document.
            for doc_chunk in doc_chunks:
                doc_len = len(document)
                if doc_chunk[1] == results['chunk_id'][ind]:
                    middle_point = doc_len + len(doc_chunk[0]) / 2
                document = document + doc_chunk[0] + "\n"
            metadata['contextbuilder']['documents_generated'].append(document)

            # Add the document to the context.
            if len(document) + len(context) <= context_size:
                context = context + document + "\n"

            else:
                # The whole document is too much to add to context. Find out how much we can add.
                context_left = context_size - len(context)
                # Extract this amount from the document with the middle point as the center.
                start = middle_point - context_left / 2
                end = middle_point + context_left / 2
                to_add = document[int(start):int(end)]
                context = context + to_add + "\n"
                # We've exhausted the context.
                break
        final_context = context[:context_size]
        metadata['contextbuilder']['context'] = final_context
        metadata['contextbuilder']['context_length'] = len(final_context)
        return final_context, metadata
