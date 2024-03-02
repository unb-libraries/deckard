# deckard
<p align="center">
<img src="assets/image.png" alt="drawing" width="400"/>

## Introduction
Deckard collects and exposes local knowledge sets via an API by leveraging modern LLMs to model end-user intent.

## Documentation
Documentation is available [in the documentation folder](./documentation/README.md "Project Documentation").

## CLI Commands
### Start API Server
Start the API server:

```
poetry run api:start
```

### Direct LLM Query
#### (Requires: API Server Running)
Query the LLM model directly without a rag pipeline:

```
poetry run query:llm <query> <optional context>

Examples:
poetry run query:llm 'Who is Donald Sutherland?'
poetry run query:llm 'Who is Donald Sutherland?' 'Donald sutherland is a duck'
```

### RAG Query
#### (Requires: API Server Running)
Query the configured RAG pipeline:

```
poetry run query:rag <pipeline> <query>

Examples:
poetry run query:rag libpages 'Where is the bathroom?'
poetry run query:rag libpages 'Who is the dean of UNB libraries?'
```

### Search Embeddings
Search the RAG pipeline embeddings database directly:

```
poetry run search:embeddings <pipeline> <query>

Example:
poetry run search:embeddings libpages 'Who is the dean of UNB libraries?'
```

### Build RAG data
Build the RAG pipeline's underlying data to ready it for use. This may have
requirements such as network requests, database tunnels, or on-disk data files.

```
poetry run build:rag <pipeline>

Example:
poetry run build:rag libpages
```

### Start Slackbot
#### (Requires: API Server Running)
Start the slackbot configured locally. Slack auth tokens need to be in ENV:

```
poetry run slackbot:start
```

## License
- As part of our 'open' ethos, UNB Libraries licenses its applications and workflows to be freely available to all whenever possible.
- Consequently, this repository's contents [unb-libraries/deckard.lib.unb.ca] are licensed under the [MIT License](http://opensource.org/licenses/mit-license.html). This license explicitly excludes:
   - Any generated content remains the exclusive property of its author(s).
   - The UNB logo and associated suite of visual identity assets remain the exclusive property of the University of New Brunswick.
