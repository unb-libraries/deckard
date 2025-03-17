# RAG Query Processing

1. **Query Reception**:
   - The system receives queries through its API endpoint.

2. **Malicious Intent Classification**:
   - Upon receiving a query, Deckard first classifies it for any malicious intent using the `MaliciousClassifier`. The system issues a standard fail response if the query is deemed unsafe.

3. **Compound Query Classification**:
   - If the query is safe, the `CompoundClassifier` verifies whether it contains multiple distinct sub-queries. If compound queries are identified, they are extracted and processed individually.

4. **Embedding Search**:
   - The system employs the `StandardQueryProcessor` to preprocess the query for embedding search. Subsequently, the query is encoded into a vector representation using the `SentenceTransformerEncoder`.
   - The encoded query is utilized to search the vector database (`LanceDB`) and retrieve pertinent documents. The results are re-ranked according to their relevance to the query.

5. **Sparse Search**:
   - In parallel, the system performs a sparse search using the `SolrClient`. This involves searching the `document` and `document_ngram` fields in the Solr index to find relevant documents.

6. **Context Building**:
   - The results retrieved from embedding and sparse searches are combined to create a context for the query. The `ContextBuilder` component selects the most relevant information to construct a coherent context.

7. **LLM Query**:
   - The constructed context and the original query are passed to the LLM chain (`LLMChain`) for inference. The LLM generates a response based on the supplied context.

8. **Response Verification**:
   - The produced response is verified by the `ResponseVerifier` to ensure it directly addresses the query. If the response is valid, it is processed further; otherwise, the system may attempt to refine the query or deliver a failed response.

9. **Response Summarization**:
   - The `CompoundResponseSummarizer` processes the final response, summarizing it when necessary to ensure clarity and conciseness.

10. **Response Delivery**:
    - The processed and verified response and any relevant metadata (e.g., source URLs) are returned to the user.
