# @NOTE: This method does not work well with chunk overlap.
from contextbuilders.SimpleContextAggregator import SimpleContextAggregator
from contextdatabases.ContextDatabase import ContextDatabase
from pandas import DataFrame as Dataframe

class ParentDocumentAssembler(SimpleContextAggregator):
    def buildContext(
            self,
            results: Dataframe,
            database: ContextDatabase,
            context_size: int
        ):
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
