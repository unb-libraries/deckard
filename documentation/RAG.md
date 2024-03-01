# RAG Details and Considerations
Modern RAG standars change quickly and the complexity of a function pipeline is quite high. The reality is a simple RAG model generally produces poor results.

To improve a RAG pipeline's results, consider the following steps/processes:

## Content Pre-Processing
## Strip formatting and links from chunks
Webpages assert links and improved results are seen when stripping links.

## Chunk Generation
### Chunk Size
Starting Rule of thumb - does a collector's data unit:
* Generally contain one, targed semantic concept? Is only one data unit likely to provide enough context for a typical query?
  * Keep chunk size high
* Generally contain many concepts? Is the LLM likely to need information from multiple other documents to answer accurately?
  * Keep chunk size low

### Chunk Re-Assembly
Simple Method (SimpleContextAggregator): Pick a maximum context size and join top X chunks.

Fancy Method (ParentDocumentAssembler): Index parent documents, then sequentially ID the chunks.

When it comes time to generate context, start by reconstructing the first result's parent document by building out neighbour chunk text values. If the whole document was reconstructued, and if context space still exists, move on to the next ranked result.

Some good thoughts here:

https://www.reddit.com/r/MachineLearning/comments/1adtuzr/d_how_to_divide_a_chunk_for_rag/


## Reranking
Re-ranking is standard now in RAG. Use a faster bi-encoder to broadly query X results
from the vector database, then encode all results with a cross-encoder again and compute similarity. "computes more fine-grained interactions between the query tokens and each document’s tokens".

## Models
The recommendations for models changes fast and furious.

* https://huggingface.co/spaces/mteb/leaderboard

The most relevant scoring for this use is the 'STS Scores': Spearman correlation based on cosine similarity.

### Embeddings
sentence-transformers/all-MiniLM-L12-v2
hkunlp/instructor-large
BAAI/bge-large-en-v1.5
avsolatorio/GIST-large-Embedding-v0 (built on BAAI-bge)

### Rerankers
colbert-ir/colbertv2.0
BAAI/bge-reranker-large

## Query Tranformations/Chaining
This is where the real secret sauce gets made. We do not simply pass raw queries to the chain, instead pre-processing the query somehow.

* Removing interrogatives from queries seems to help when similarity matching (to be explored)
* Understanding that the user may not query optimally for the LLM and use a LLM to distill the query into a more reasonable query
* Chain LLM queries to classify queries and adadptively transform.

* https://blog.langchain.dev/query-transformations/
