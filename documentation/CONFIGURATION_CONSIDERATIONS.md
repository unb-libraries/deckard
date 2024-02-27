# Configuration

## Strip links from chunks
Webpages assert links and improved results are seen when stripping links.


## Context Chunk Size
Is a single RAG document:
* likely to address a typical question? Keep chunk size high (2048) (2 chunks in context space)
* likely to need information from multiple other documents to answer accurately? Keep context low(512) (8 chunks in context space)
* Othewise, 1024 is a good starting point

## Chunk Generation
https://www.reddit.com/r/MachineLearning/comments/1adtuzr/d_how_to_divide_a_chunk_for_rag/

A great thought here. Intead of relying on Overlap and assembling confusing context snippets as we do in LanceDB class

Instead, index parent documents, then sequentially ID the chunks.

When it comes time to generate context, start by reconstructing the first result's parent document by building out neighbour chunk text values. If the whole document was reconstructued, and if context space still exists, move on to the next ranked result.

