#!/bin/bash

SOLR_URL="http://localhost:3514/solr"
CORE_NAME="deckard"

echo "🛠 Adding field types..."

# Define text_general (Standard text processing)
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-field-type": {
    "name": "text_general",
    "class": "solr.TextField",
    "analyzer": {
      "tokenizer": { "class": "solr.StandardTokenizerFactory" },
      "filters": [
        { "class": "solr.LowerCaseFilterFactory" }
      ]
    }
  }
}' "$SOLR_URL/$CORE_NAME/schema"

# Define ngram_text (For document_ngram)
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-field-type": {
    "name": "ngram_text",
    "class": "solr.TextField",
    "analyzer": {
      "tokenizer": { "class": "solr.StandardTokenizerFactory" },
      "filters": [
        { "class": "solr.LowerCaseFilterFactory" },
        { "class": "solr.NGramFilterFactory", "minGramSize": 3, "maxGramSize": 10 }
      ]
    }
  }
}' "$SOLR_URL/$CORE_NAME/schema"

echo "🛠 Adding fields..."

# Define ID field
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-field": {
    "name": "id",
    "type": "uuid",
    "indexed": true,
    "stored": true,
    "required": true
  }
}' "$SOLR_URL/$CORE_NAME/schema"

# Define document_id field
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-field": {
    "name": "document_id",
    "type": "string",
    "indexed": true,
    "stored": true
  }
}' "$SOLR_URL/$CORE_NAME/schema"

# Define document field
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-field": {
    "name": "document",
    "type": "text_general",
    "indexed": true,
    "stored": true
  }
}' "$SOLR_URL/$CORE_NAME/schema"

curl -X POST -H "Content-Type: application/json" --data '{
  "add-field": {
    "name": "chunk_id",
    "type": "string",
    "indexed": true,
    "stored": true
  }
}' "$SOLR_URL/$CORE_NAME/schema"

# Define metadata field
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-field": {
    "name": "metadata",
    "type": "text_general",
    "indexed": true,
    "stored": true
  }
}' "$SOLR_URL/$CORE_NAME/schema"

# Define document_ngram field
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-field": {
    "name": "document_ngram",
    "type": "ngram_text",
    "indexed": true,
    "stored": false
  }
}' "$SOLR_URL/$CORE_NAME/schema"

echo "🔄 Copying document -> document_ngram..."
curl -s -X POST -H "Content-Type: application/json" --data '{
  "add-copy-field": {
    "source": "document",
    "dest": "document_ngram"
  }
}' "$SOLR_URL/$CORE_NAME/schema"

curl -X POST -H "Content-Type: application/json" --data '{
  "add-field-type": {
    "name": "text_stemmed",
    "class": "solr.TextField",
    "analyzer": {
      "tokenizer": { "class": "solr.StandardTokenizerFactory" },
      "filters": [
        { "class": "solr.LowerCaseFilterFactory" },
        { "class": "solr.StopFilterFactory", "ignoreCase": true, "words": "stopwords.txt", "format": "wordset" },
        { "class": "solr.PorterStemFilterFactory" }
      ]
    }
  }
}' "$SOLR_URL/$CORE_NAME/schema"

curl -X POST -H "Content-Type: application/json" --data '{
  "add-field": {
    "name": "document_stemmed",
    "type": "text_stemmed",
    "indexed": true,
    "stored": true
  }
}' "$SOLR_URL/$CORE_NAME/schema"

curl -X POST -H "Content-Type: application/json" --data '{
  "add-copy-field": {
    "source": "document",
    "dest": "document_stemmed"
  }
}' "$SOLR_URL/$CORE_NAME/schema"

echo "🔄 Reloading Solr core..."
curl -s "$SOLR_URL/admin/cores?action=RELOAD&core=$CORE_NAME"

echo "✅ Solr schema setup completed!"
