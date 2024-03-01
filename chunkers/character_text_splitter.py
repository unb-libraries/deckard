"""Provides the CharacterTextSplitterChunker class."""
import hashlib
import json
import os
from logging import Logger
from typing import TypeVar

from langchain.text_splitter import CharacterTextSplitter

from core.config import get_data_dir

T = TypeVar('T', list, list, dict)

class CharacterTextSplitterChunker:
    """Generates chunks from text using CharacterTextSplitter.

    Args:
        config (dict): The configuration for the chunker.
        log (Logger): The logger for the chunker.

    Attributes:
        config (dict): The configuration for the chunker.
        log (Logger): The logger for the chunker.

    .. data:: OUTPUT_PATH
        The path to write the chunks to.
    """

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
    ) -> T :
        """Generates chunks from the content and metadata.

        Args:
            content (str): The content to generate chunks from.
            metadata (dict): The metadata to generate chunks from.

        Returns:
            T: The generated chunks, the raw chunks, and the metadata.
        """
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
            self._write_chunks_to_disk(chunks, self.OUTPUT_PATH)

        return chunks, raw_chunks, metadata

    @staticmethod
    def _write_chunks_to_disk(chunks: list, output_path: str) -> None:
        """Writes the chunks to disk.

        Args:
            chunks (list): The chunks to write to disk.
            output_path (str): The path to write the chunks to.
        """
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        hash_rep = hashlib.md5(json.dumps(chunks, sort_keys=True).encode('utf-8')).hexdigest()
        for i, chunk in enumerate(chunks):
            output_filename = os.path.join(
                output_path,
                hash_rep
            ) + f'_{i}.txt'
            with open(output_filename, 'w', encoding="utf-8") as f:
                f.write(chunk)
