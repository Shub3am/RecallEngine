# RecallEngine Usage Guide

## Install

```bash
pip install "recall-engine[all] @ git+https://github.com/Shub3am/RecallEngine"
```

Drop `[all]` for a keyword and ranked only install, or pick `[semantic]` or `[api]` on their own.

---

## Library API

### 1. Create an engine

```python
from recall_engine import SearchEngine

engine = SearchEngine.from_json(
    "datasets/movies.json",
    data_key="movies",        # top-level key in the JSON that holds the list of docs
    doc_id_key="id",          # field used as the unique document identifier
    exclude_doc_keys=["id"],  # fields to skip when indexing text content
)
```

`from_json` loads the cached index from `~/.cache/recall_engine/index.pkl` when it was built from the same file (path, size and modification time) with the same options. Otherwise it rebuilds and saves it. Pass `cache_path=` to keep a separate cache per dataset.

For documents already in memory, nothing touches disk:

```python
engine = SearchEngine.from_documents(documents, doc_id_key="id")
```

---

### 2. Keyword search

Returns all documents containing any of the query terms, sorted by document id.

```python
for doc in engine.search("dark knight", mode="keyword"):
    print(doc["title"])
```

---

### 3. Boolean search

Supports `AND`, `OR`, `NOT` and parentheses. Operators must be uppercase.

```python
engine.search("crime AND drama", mode="boolean")
engine.search("comedy OR horror", mode="boolean")
engine.search("action AND NOT comedy", mode="boolean")
engine.search("(crime OR drama) AND NOT comedy", mode="boolean")
```

A malformed query, such as an unmatched parenthesis, raises `ValueError`.

---

### 4. Ranked search: BM25

BM25 scores documents by relevance, rewards rare terms and normalizes for document length.

```python
for doc in engine.search("bank regulation financial market", mode="bm25", top_k=5):
    print(f"[{doc['rank']}] score={doc['score']:.4f} | {doc['title']}")
```

Each ranked result includes two extra fields:
- `score`: relevance score, higher is better
- `rank`: position in the result list, starting from 1

---

### 5. Ranked search: TF-IDF

A simpler scoring baseline, useful for comparison against BM25.

```python
engine.search("immune system lymph nodes", mode="tfidf", top_k=5)
```

---

### 6. Semantic search

Ranks documents by embedding similarity, so it finds matches that share meaning but no words. Needs the `semantic` extra.

```python
engine.search("films about exploring outer space", mode="semantic", top_k=5)
```

The default model is `BAAI/bge-small-en-v1.5` through fastembed. It runs locally on CPU; the first use downloads it (about 70 MB). Document embeddings are computed once. For engines built with `from_json` they are saved next to the index cache and reused until the dataset or the model changes.

To use a different model, pass any object with fastembed's `passage_embed` and `query_embed` methods:

```python
from fastembed import TextEmbedding

engine = SearchEngine.from_json("docs.json", embedding_model=TextEmbedding("BAAI/bge-base-en-v1.5"))
```

---

### 7. Hybrid search

Runs BM25 and semantic search, takes the top 100 of each and merges them with Reciprocal Rank Fusion (k = 60). It finds exact term matches and paraphrases in one query.

```python
engine.search("space travel", mode="hybrid", top_k=5)
```

`score` is the fused RRF score, so it is only comparable between results of the same query.

---

### 8. Auto mode

The default. Queries with `AND`, `OR`, `NOT`, `(` or `)` go to boolean, everything else to keyword.

```python
engine.search("apple AND banana")  # boolean
engine.search("dark knight")       # keyword
```

---

### 9. top_k

`top_k` limits the number of results for `bm25`, `tfidf`, `semantic` and `hybrid`. It must be a positive integer; `0` or a negative number raises `ValueError`.

---

### 10. Dataset shape

Any JSON file works as long as it contains a list of documents:

```json
{
  "docs": [
    { "id": "1", "title": "First Document", "text": "..." },
    { "id": "2", "title": "Second Document", "text": "..." }
  ]
}
```

A flat list at the top level also works; leave out `data_key`:

```python
engine = SearchEngine.from_json("path/to/flat.json")
```

---

### 11. Using the Indexer directly

`SearchEngine` is a facade over `Indexer`, which gives lower-level access:

```python
from recall_engine.search_engine import Indexer

indexer = Indexer()
indexer.load_or_build("datasets/movies.json", dataKey="movies", docIdKey="id")

indexer.get_documents("action hero", operation="OR")
indexer.get_index()                 # dict[term -> list[doc_id]]
indexer.get_doc_map()               # dict[doc_id -> document]
indexer.get_term_frequencies()      # dict[term -> dict[doc_id -> count]]
indexer.get_document_frequencies()  # dict[term -> int]
```

---

## CLI

```bash
recall_engine search "action hero" --dataset datasets/movies.json --data-key movies
recall_engine search "space travel" --mode hybrid --top-k 5
recall_engine serve --dataset datasets/movies.json --data-key movies --host 127.0.0.1 --port 8000
```

`--mode` accepts every mode in the table below and defaults to `bm25`. `python -m recall_engine` works the same way.

---

## HTTP API

`recall_engine serve` starts a FastAPI app with uvicorn. Needs the `api` extra.

| Method | Path      | Body                                        | Returns |
|--------|-----------|---------------------------------------------|---------|
| GET    | `/health` |                                             | `{"status": "ok", "documents": <count>}` |
| POST   | `/search` | `{"query": str, "mode": str, "top_k": int}` | `{"query", "mode", "count", "results"}` |

`mode` defaults to `auto` and `top_k` is optional. An unknown mode, a non-positive `top_k` or a malformed boolean query returns 400. A missing `query` returns 422. OpenAPI docs are at `/docs`.

### Authentication

Set `RECALL_ENGINE_API_KEY` in the server's environment. `/search` then requires a matching `X-API-Key` header and returns 401 otherwise. `/health` stays open.

```bash
RECALL_ENGINE_API_KEY=change-me recall_engine serve --dataset docs.json --data-key docs
curl -X POST localhost:8000/search -H 'X-API-Key: change-me' -H 'content-type: application/json' -d '{"query": "apple"}'
```

### Embedding in your own service

```python
from recall_engine import SearchEngine
from recall_engine.api import create_app

app = create_app(SearchEngine.from_json("docs.json", data_key="docs"), api_key="change-me")
# run with: uvicorn my_module:app --workers 4
```

Each uvicorn worker is a separate process that loads its own copy of the index.

---

## Search Mode Reference

| Mode       | Description                                         | Supports `top_k` | Extra      |
|------------|-----------------------------------------------------|------------------|------------|
| `auto`     | Detects boolean operators, falls back to keyword    | No               |            |
| `keyword`  | Union of matched terms, sorted by doc id            | No               |            |
| `boolean`  | AND / OR / NOT operators, sorted by doc id          | No               |            |
| `bm25`     | Ranked by BM25 score                                | Yes              |            |
| `tfidf`    | Ranked by TF-IDF score                              | Yes              |            |
| `semantic` | Ranked by embedding cosine similarity               | Yes              | `semantic` |
| `hybrid`   | BM25 and semantic merged with Reciprocal Rank Fusion | Yes             | `semantic` |
