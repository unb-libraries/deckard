import hashlib
import json
import os

from langchain.text_splitter import CharacterTextSplitter
from core.config import get_data_dir

class StandardChunker:
    OUTPUT_PATH = os.path.join(
        get_data_dir(),
        'chunkers',
        'standard',
        'output'
    )

    def __init__(self, log):
        self.log = log

    def generate(
        self,
        content,
        metadata,
        split_on,
        chunk_size,
        overlap,
        add_document_metadata=False,
        write_chunks=True
    ):
        text_splitter = CharacterTextSplitter(split_on, chunk_size=chunk_size, chunk_overlap=overlap)
        raw_chunks = text_splitter.split_text(content)
        self.log.info(f"Generated {len(raw_chunks)} chunks from content.")

        chunks = []
        if 'title' in metadata and add_document_metadata:
            for raw_chunk in raw_chunks:
                chunks.append(metadata['title'] + "\n\n" + raw_chunk)
        else:
            chunks = raw_chunks

        if write_chunks:
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
