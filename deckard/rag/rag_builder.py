from logging import Logger

from deckard.core import load_class
from deckard.core.utils import clear_gpu_memory
from deckard.core.utils import gen_uuid

class RagBuilder:
    """Builds the data for a RAG pipeline.

    Args:
        config (dict): The pipeline configuration.
        log (Logger): The logger.

    Attributes:
        config (dict): The configuration.
        log (Logger): The logger.
        database (EmbeddingDatabase): The database for the embeddings.
        context_database (ContextDatabase): The database for the contexts.
        encoder (EmbeddingEncoder): The encoder for the embeddings.
        chunker (Chunker): The chunker for the documents.
        collectors (list): The collectors for the documents.
    """
    def __init__(
        self,
        config: dict,
        log: Logger
    ):
        self.log = log
        self.config = config
        self._init_rag_builder_components()

    def build(self) -> None:
        """Builds the RAG pipeline."""
        self.database.flush_data()
        self.context_database.flush_data()
        self.sparse_search.flush_data()

        for collector in self.collectors:
            self.log.info("Processing collector %s", collector.name())
            first_item = True
            embedding_id = 0
            total_items = collector.len()
            if total_items == 0:
                self.log.warning("Collector provided no items to process.")
                return
            processed_items = 0
            pipeline_id = 0
            for document_content, metadata in collector:
                document = {'id': gen_uuid()}

                if document_content is None:
                    self.log.warning("Item %s is None, skipping.", pipeline_id)
                    continue
                if collector.ignore_item(document_content):
                    self.log.info("Ignoring item %s", document_content)
                    continue
                self.log.info("Processing item %s of %s", pipeline_id, total_items)
                processed_items += 1

                document['chunks'], document['raw_chunks'], document['metadata'] = self.chunker.generate(
                    document_content,
                    metadata
                )

                if len(document['chunks']) > 0:
                    document['embeddings'] = []
                    for chunk in document['chunks']:
                        clear_gpu_memory()
                        document['embeddings'].append(self.encoder.encode(chunk))

                    embedding_id = self.database.add_embeddings(
                        document,
                        embedding_id,
                        first_item
                    )

                    self.context_database.add_contexts(
                        document,
                        first_item
                    )

                    self.sparse_search.index_document(
                        document
                    )

                    if first_item:
                        first_item = False
                    pipeline_id += 1

        ignored_items = total_items - processed_items
        self.log.info("Processed %s items, ignored %s items.", processed_items, ignored_items)
        self.log.info("Pipeline Processing Complete.")

    def _init_rag_builder_components(self) -> None:
        """Initializes the components for building the RAG pipeline."""
        self.encoder = load_class(
            self.config['embedding_encoder']['module_name'],
            self.config['embedding_encoder']['class_name'],
            [
                self.config['embedding_encoder']['model'],
                self.log
            ]
        )

        self.database = load_class(
            self.config['embedding_database']['module_name'],
            self.config['embedding_database']['class_name'],
            [
                self.config['embedding_database']['name'],
                self.log,
                True
            ]
        )

        self.sparse_search = load_class(
            self.config['sparse_search']['module_name'],
            self.config['sparse_search']['class_name'],
            [
                self.config['sparse_search']['uri'],
                self.log,
                True
            ]
        )

        self.context_database = load_class(
            self.config['context_database']['module_name'],
            self.config['context_database']['class_name'],
            [
                self.config['context_database']['name'],
                self.log,
                True
            ]
        )

        self.chunker = load_class(
            self.config['chunker']['module_name'],
            self.config['chunker']['class_name'],
            [
                self.config['chunker']['config'],
                self.log
            ]
        )

        self.collectors = []
        for collector in self.config['collectors']:
            self.collectors.append(
                load_class(
                    collector['module_name'],
                    collector['class_name'],
                    [
                        collector['config'],
                        self.log
                    ]
                )
            )
