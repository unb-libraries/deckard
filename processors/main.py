import json
import sys

from core.config import get_workflow_chunker
from core.config import get_workflow_collectors
from core.config import get_workflow_db
from core.config import get_workflow_context_db
from core.config import get_workflow_encoder
from core.config import get_workflows
from core.config import get_workflow
from core.logger import get_logger
from core.utils import clear_gpu_memory
from secrets import token_hex

CMD_STRING = 'build:rag'

def start(args=sys.argv):
    log = get_logger()
    validate_args(args, log)

    workflow = get_workflow(args[1])
    log.info(f"Building Endpoint {workflow['name']}")

    chunker = get_workflow_chunker(workflow['name'], log)
    sentence_encoder = get_workflow_encoder(workflow['name'], log)
    vector_database = get_workflow_db(workflow['name'], log)
    vector_database.flushData()
    context_database = get_workflow_context_db(workflow['name'], log, True)
    context_database.flushData()

    for collector in get_workflow_collectors(workflow['name'], log):
        log.info(f"Processing collector {collector.name()}")
        first_item = True
        embedding_id = 0
        total_items = collector.len()
        if total_items == 0:
            log.warning("Collector provided no items to process.")
            return
        processed_items = 0
        id = 0
        for document_content, metadata in collector:
            document = {'id': token_hex(32)}

            if document_content is None:
                log.warning(f"Item {id} is None, skipping.")
                continue
            if collector.ignoreItem(document_content):
                log.info(f"Ignoring item {document_content}")
                continue
            log.info(f"Processing item {id} of {total_items}")
            processed_items += 1

            document['chunks'], document['raw_chunks'], document['metadata'] = chunker.generate(
                document_content,
                metadata,
                "\n",
                workflow['rag']['chunker']['size'],
                workflow['rag']['chunker']['overlap'],
            )

            if len(document['chunks']) > 0:
                document['embeddings'] = []
                for chunk in document['chunks']:
                    clear_gpu_memory()
                    document['embeddings'].append(sentence_encoder.encode(chunk))

                embedding_id = vector_database.addEmbeddings(
                    document,
                    embedding_id,
                    first_item
                )

                context_database.addContexts(
                    document,
                    first_item
                )
                if first_item:
                    first_item = False
                id += 1

    ignored_items = total_items - processed_items
    log.info(f"Processed {processed_items} items, ignored {ignored_items} items.")
    log.info("Workflow Processing Complete.")

def validate_args(args, log):
    if len(args) < 2:
        log.warning(f"Usage: poetry run {CMD_STRING} <workflow>")
        print_get_workflows(log, workflows)
        sys.exit(1)

    workflows = get_workflows()
    if args[1] not in workflows:
        log.error(f"Endpoint {args[1]} not found")
        print_get_workflows(log, workflows)
        sys.exit(1)

def print_get_workflows(log, workflows):
    log.warning("Available endpoints:")
    for workflow in workflows:
        log.warning(f"  {workflow}")
