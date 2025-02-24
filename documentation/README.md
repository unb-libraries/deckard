# Documentation
(This is a work in progress).

## Topics
* [Technical Prerequisites, Guidance](./TECHNICAL_PREREQUISITE_GUIDANCE.md "Technical Prerequisites, Guidance")
* [Source Content Considerations](./CONTENT_CONSIDERATIONS.md "Source Content Considerations")
* [RAG Pipeline Considerations](./RAG.md "RAG Pipeline Considerations")
* [Project Design Considerations](./PROJECT_DESIGN_CONSIDERATIONS.md "Project Design Considerations")

## Overview
Deckard's architecture is based on a core concept of 'data units': representations of one or more ideas in textual form.

## RAG pipeline
### Collectors
Collectors collect data units from source(s) and transform them into pure textual representations. Modules can be written to access data via the web, from a database, or another endpoint. Pipelines can leverage multiple collectors.

### Chunkers
Chunkers divide data units into fragments of the original data unit. These fragments are called 'chunks'. By chunking data, we:

* Allow relevant information from the data unit's content to fit within the (limited) LLM context space.
* Segregate semantic concepts within the data unit for improved matching in the RAG pipeline.

### Encoders
Encoders map chunks into vector representations.

jina-embeddings-v3
mxbai-embed-large-v1


### Databases
Database modules provide API interfaces into local storage.

### Interfaces
Interfaces expose data to users.

### RAG Builders
RAG builders build the underlying data necessary for rag queries.

