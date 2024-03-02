from logging import Logger

from pandas import DataFrame
from sentence_transformers import SentenceTransformer, util as st_util
from torch import Tensor

from deckard.core.utils import clear_gpu_memory

class SentenceTransformerEncoder:
    """Encodes text using the Sentence Transformer model.

    Args:
        model (str): The name of the Sentence Transformer model to use.
        log (Logger): The logger for the encoder.

    Attributes:
        encoder (SentenceTransformer): The Sentence Transformer model to use.
        log (Logger): The logger for the encoder.
    """

    def __init__(self, model: str, log: Logger) -> None:
        self.log = log
        log.info("Loading Sentence Transformer Model: %s", model)
        self.encoder = SentenceTransformer(
            model,
            device='cuda'
        )

    def encode(self, value: str) -> Tensor:
        """Encodes a textual value into a Tensor.

        Args:
            value (str): The value to encode.

        Returns:
            Tensor: The encoded value.
        """
        return self.encoder.encode(value)

    def rerank(self, query: str, results: DataFrame) -> DataFrame:
        """Reranks the results based on the query.

        Args:
            query (str): The query to use for reranking.
            results (DataFrame): The results to rerank.

        Returns:
            DataFrame: The reranked results, sorted by a new column 'rerank_score'.
        """
        new_scores = []
        self.log.info("Reranking Results: %s", query)
        for ind in results.index:
            clear_gpu_memory()
            result_text = results['text'][ind]
            new_scores.append(self._compute_similarity(query, result_text))
        results.insert(2, "rerank_score", new_scores, True)
        return results.sort_values(by=["rerank_score"], ascending=False)

    def _compute_similarity(self, query: str, text:str) -> float:
        """Computes the similarity between the query and the text.

        Args:
            query (str): The query.
            text (str): The text to compare to the query.

        Returns:
            float: The similarity score.
        """
        query_vector = self.encode(query)
        text_vector = self.encode(text)
        return st_util.cos_sim(query_vector, text_vector).item()
