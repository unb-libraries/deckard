# deckard
<p align="center">
<img src="assets/image.png" alt="drawing" width="400"/>

## Introduction
Deckard collects and exposes local knowledge by leveraging modern LLMs. It uses a hybrid Retrieval-Augmented Generation (RAG) approach to process queries and generate accurate, contextually relevant responses. 

## Documentation
Some stub documentation is currently available [in the documentation folder](./documentation/README.md "Project Documentation"). Notable topics:
* For information on how queries are processed, see the [RAG Query Processing](./documentation/RAG_QUERY_STEPS.md "RAG Query Processing") document.
* For details on how the RAG pipeline is built, see the [RAG Data Building Process](./documentation/RAG_INDEXING_STEPS.md "RAG Data Building Process") document.

## Pre-requisites
- Python 3.8+
- [Poetry](https://python-poetry.org/docs/)
- [Nvidia drivers](https://www.nvidia.com/Download/index.aspx)
- [CUDA](https://developer.nvidia.com/cuda-downloads)

## CLI Commands
### `api:start`

Start the API server:

`poetry run api:start`


### `build:rag`
Build the RAG pipeline's underlying data to ready it for use. This may have
requirements such as network requests, database tunnels, or on-disk data files.

`poetry run build:rag <pipeline>`
```
poetry run build:rag libpages
```

## Convenience Commands
Other commands are available for convenience:

### `query:rag`
#### (API Server Must be Running)
Query the configured RAG pipeline:

`poetry run query:rag <pipeline> <query>`

```
poetry run query:rag libpages 'Where is the bathroom?'
poetry run query:rag libpages 'Who is the dean of UNB libraries?'
```

### `query:llm`
#### (API Server Must be Running)
Query the LLM model directly without a rag pipeline:

`poetry run query:llm <query> <optional context>`

```
poetry run query:llm 'Who is Donald Sutherland?'
poetry run query:llm 'Who is Donald Sutherland?' 'Donald sutherland is a duck'
```

### `slackbot:start`
#### (API Server Must be Running)
Start the slackbot configured locally. Slack auth tokens need to be in ENV:

`poetry run slackbot:start`


## License
- In line with our 'open' ethos, UNB Libraries makes its applications and workflows freely available to everyone whenever possible.
- As a result, the contents of this repository [unb-libraries/deckard] are licensed under the [MIT License](http://opensource.org/licenses/mit-license.html). This license explicitly excludes:
   - Any content that remains the exclusive property of its author(s).
   - The UNB logo and any associated visual identity assets remain the exclusive property of the University of New Brunswick.
