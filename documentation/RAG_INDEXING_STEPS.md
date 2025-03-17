# RAG Data Building Process

1. **Data Collection**:
   - Collectors retrieve data units from their respective sources. This data is typically in raw text, HTML, or other formats that need to be processed [1].

2. **Chunk Generation**:
   Using the `Chunker` component, the collected data units are separated into smaller parts known as "chunks." Chunking ensures that relevant information fits within the restricted context space of the LLM and differentiates semantic concepts for better matching in the RAG pipeline.
   - The `Chunker` processes each data unit to generate chunks, raw chunks, and associated metadata [2].

3. **Embedding Generation**:
   - Each chunk is encoded as a vector representation using the `EmbeddingEncoder`. This process transforms the textual chunks into numerical vectors suitable for similarity matching and retrieval.
   - The encoded embeddings are stored in the `EmbeddingDatabase` [3].

4. **Context Database Update**:
   - The `ContextDatabase` is updated with the generated chunks and their embeddings. This database is used to build the context for queries during the RAG process [4].

5. **Sparse Indexing**:
   - The system conducts sparse indexing of the collected data units using the `SolrClient`. This process includes indexing the chunks and their metadata on the Solr server, enabling them to be searchable through sparse search queries.
   - The `SolrClient` indexes both the `document` and `document_ngram` fields to facilitate efficient retrieval of relevant documents [5].

6. **Pipeline Processing**:
   - The system processes each collector's data units sequentially. For each data unit, the following steps are performed:
     - The data unit is chunked into smaller fragments.
     - Each chunk is encoded into a vector representation.
     - The embeddings are added to the `EmbeddingDatabase`.
     - The context database is updated with the chunks and embeddings.
     - The chunks and metadata are indexed in the Solr server [6].

### Key Components

- **Collectors**: Gather data units from various sources and transform them into textual representations.
- **Chunker**: Divides data units into smaller chunks for efficient processing and retrieval.
- **EmbeddingEncoder**: Encodes chunks into vector representations for similarity matching.
- **EmbeddingDatabase**: Stores the encoded embeddings for retrieval during the RAG process.
- **ContextDatabase**: Maintains the chunks and their embeddings for context building.
- **SolrClient**: Indexes chunks and metadata in the Solr server for sparse search queries.

The RAG data building process ensures that the collected data is efficiently chunked, encoded, and indexed, making it ready for use in the RAG pipeline for accurate and contextually relevant query responses.

### Further Reading

1. [Data Collection](https://en.wikipedia.org/wiki/Data_collection)
2. [Text Chunking](https://towardsdatascience.com/text-chunking-and-named-entity-recognition-using-nltk-and-conll-corpora-8b5555a6a8b3)
3. [Text Embeddings](https://towardsdatascience.com/neural-network-embeddings-explained-4d028e6f0526)
4. [Context Databases](https://en.wikipedia.org/wiki/Contextual_database)
5. [Sparse Indexing](https://lucene.apache.org/solr/guide/8_8/indexing-guide.html)
6. [Data Processing Pipelines](https://en.wikipedia.org/wiki/Data_pipeline)