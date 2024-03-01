from deckard.core.utils import clear_gpu_memory
from deckard.core import load_class
from deckard.core.utils import gen_uuid
from logging import Logger

class RagBuilder:
    def __init__(
        self,
        config: dict,
        log: Logger
    ):
        self.log = log
        self.config = config
        self.initComponents()

    def build(self) -> None:
        self.database.flushData()
        self.context_database.flushData()

        for collector in self.collectors:
            self.log.info(f"Processing collector {collector.name()}")
            first_item = True
            embedding_id = 0
            total_items = collector.len()
            if total_items == 0:
                self.log.warning("Collector provided no items to process.")
                return
            processed_items = 0
            id = 0
            for document_content, metadata in collector:
                document = {'id': gen_uuid()}

                if document_content is None:
                    self.log.warning(f"Item {id} is None, skipping.")
                    continue
                if collector.ignoreItem(document_content):
                    self.log.info(f"Ignoring item {document_content}")
                    continue
                self.log.info(f"Processing item {id} of {total_items}")
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

                    embedding_id = self.database.addEmbeddings(
                        document,
                        embedding_id,
                        first_item
                    )

                    self.context_database.addContexts(
                        document,
                        first_item
                    )
                    if first_item:
                        first_item = False
                    id += 1

        ignored_items = total_items - processed_items
        self.log.info(f"Processed {processed_items} items, ignored {ignored_items} items.")
        self.log.info("pipeline Processing Complete.")

    def initComponents(self) -> None:
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

