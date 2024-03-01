from core.utils import clear_gpu_memory
from logging import Logger
from pandas import DataFrame
from sentence_transformers import SentenceTransformer, util

class SentenceTransformerEncoder:
    def __init__(self, model: str, log: Logger) -> None:
        self.log = log
        log.info(f"Loading Sentence Transformer Model: {model}")
        self.encoder = SentenceTransformer(
            model,
            device='cuda'
        )

    def encode(self, value: str):
        return self.encoder.encode(value)

    def rerank(self, query: str, results: DataFrame) -> DataFrame:
        new_scores = []
        self.log.info(f"Reranking Results: {query}")
        for ind in results.index:
            clear_gpu_memory()
            result_text = results['text'][ind]
            new_scores.append(self.computeSimilarity(query, result_text))
        results.insert(2, "rerank_score", new_scores, True)
        return results.sort_values(by=["rerank_score"], ascending=False)

    def computeSimilarity(self, query: str, text:str) -> float:
        query_vector = self.encode(query)
        text_vector = self.encode(text)
        return util.cos_sim(query_vector, text_vector).item()
