import hashlib
import json
import os

from core.config import get_data_dir
from langchain.text_splitter import CharacterTextSplitter
from logging import Logger

class CharacterTextSplitterChunker:
    OUTPUT_PATH = os.path.join(
        get_data_dir(),
        'chunkers',
        'standard',
        'output'
    )

    def __init__(self, config: dict, log: Logger) -> None:
        self.config = config
        self.log = log

    def generate(
        self,
        content: str,
        metadata: dict
    ) -> tuple :
        text_splitter = CharacterTextSplitter(
            self.config['split_on'],
            chunk_size=self.config['chunk_size'],
            chunk_overlap=self.config['overlap']
        )
        raw_chunks = text_splitter.split_text(content)
        self.log.info(f"Generated {len(raw_chunks)} chunks from content.")

        chunks = []
        if 'title' in metadata and self.config['add_document_metadata']:
            for raw_chunk in raw_chunks:
                chunks.append(metadata['title'] + "\n\n" + raw_chunk)
        else:
            chunks = raw_chunks

        if self.config['write_chunks_to_disk']:
            if not os.path.exists(self.OUTPUT_PATH):
                os.makedirs(self.OUTPUT_PATH)
            self.log.info(f"Writing {len(chunks)} chunks to disk.")
            hash_rep = hashlib.md5(json.dumps(chunks, sort_keys=True).encode('utf-8')).hexdigest()
            for i, chunk in enumerate(chunks):
                output_filename = os.path.join(
                    self.OUTPUT_PATH,
                    hash_rep
                ) + f'_{i}.txt'
                with open(output_filename, 'w') as f:
                    f.write(chunk)

        return chunks, raw_chunks, metadata
