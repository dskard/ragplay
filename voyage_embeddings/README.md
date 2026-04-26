# voyage_embeddings

Examples from https://platform.claude.com/docs/en/build-with-claude/embeddings

## Examples

### voyageai_print_embeddings.py

Demonstrates basic usage of the Voyage AI Python client. Embeds two sample texts using the `voyage-4` model and prints the resulting embedding vectors.

**Source:** https://platform.claude.com/docs/en/build-with-claude/embeddings#voyage-python-library

### voyageai_embeddings_quick_start.py

Demonstrates semantic search using Voyage AI embeddings. Embeds a set of documents and a query, then finds the most relevant document by computing cosine similarity (dot product) between the query and document embeddings.

**Source:** https://platform.claude.com/docs/en/build-with-claude/embeddings#quickstart-example

## Setup

Requires a Voyage AI API key set as the `VOYAGE_API_KEY` environment variable.

```
just setup
```

## Running examples

```
just run-print-embeddings
just run-quick-start
```
