from core.utils import clear_gpu_memory
from core.classloader import load_class
from core.utils import gen_uuid

class RagBuilder:
    def __init__(self, config, log):
        self.log = log
        self.config = config
        self.initComponents()

    def build(self):
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
        self.log.info("Workflow Processing Complete.")

    def initComponents(self):
        self.encoder = load_class(
            'encoders',
            self.config['embedding_encoder']['classname'],
            [
                self.config['embedding_encoder']['model'],
                self.log
            ]
        )
        self.database = load_class(
            'vectordatabases',
            self.config['embedding_database']['classname'],
            [
                self.config['embedding_database']['name'],
                self.log,
                True
            ]
        )
        self.context_database = load_class(
            'contextdatabases',
            self.config['context_database']['classname'],
            [
                self.config['context_database']['name'],
                self.log,
                True
            ]
        )

        self.chunker = load_class(
            'chunkers',
            self.config['chunker']['classname'],
            [
                self.config['chunker']['config'],
                self.log
            ]
        )

        self.collectors = []
        for collector in self.config['collectors']:
            self.collectors.append(
                load_class(
                    'collectors',
                    collector['classname'],
                    [
                        collector['config'],
                        self.log
                    ]
                )
            )

