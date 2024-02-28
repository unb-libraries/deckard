# RAG

## Chunk Size

## Reranking
For this, Colbertv2 is a great choice: instead of a bi-encoder like our classical embedding models, it is a cross-encoder that computes more fine-grained interactions between the query tokens and each document’s tokens.

## Models
https://huggingface.co/spaces/mteb/leaderboard

STS Scores are relevant for our use. Spearman correlation based on cosine similarity.

### Embeddings

sentence-transformers/all-MiniLM-L12-v2
hkunlp/instructor-large
BAAI/bge-large-en-v1.5
avsolatorio/GIST-large-Embedding-v0 (built on BAAI-bge)

### Rerankers
colbert-ir/colbertv2.0
BAAI/bge-reranker-large

## Models/Combinations

| Embedding Model                         | Average Embedding Time (1024) | Rerank Model | Average Query Time | Results |
| --------------------------------------- | ----------------------------- | ------------ | ------------------ | ------- |
| sentence-transformers/all-MiniLM-L12-v2 | y                             | z            | a                  | f       |
|                                         |                               |              |                    |         |
|                                         |                               |              |                    |         |
