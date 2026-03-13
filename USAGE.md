# RecallEngine Usage Guide

## Install

```bash
git clone https://github.com/Shub3am/RecallEngine
cd RecallEngine
poetry install --with dev
```

---

## CLI

The CLI works against the bundled movies dataset by default.

```bash
# Keyword search
poetry run recall_engine search "action hero"

# Module-style equivalent
poetry run python -m recall_engine search "action hero"
```

---

## Library API

### 1. Setup — build or load an index

```python
from recall_engine.search_engine import SearchEngine

engine = SearchEngine()

# Build a fresh index from a JSON dataset and persist it to cache.
engine.build_index(
    doc_path="datasets/movies.json",
    data_key="movies",       # top-level key in the JSON that holds the list of docs
    doc_id_key="id",         # field used as the unique document identifier
    exclude_doc_keys=["id"], # fields to skip when indexing text content
    persist=True,            # save index to disk so the next run can load it
)

# Or: load from cache if it exists, otherwise build and save automatically.
engine.load_or_build_index(
    doc_path="datasets/movies.json",
    data_key="movies",
    doc_id_key="id",
    exclude_doc_keys=["id"],
)
```

---

### 2. Keyword search

Returns all documents containing any of the query terms. Results are sorted by document ID.

```python
results = engine.search("dark knight", mode="keyword")

for doc in results:
    print(doc["title"])
```

---

### 3. Boolean search

Supports `AND`, `OR`, `NOT` operators and parentheses for grouping.
Operators must be uppercase.

```python
# Documents containing both terms
results = engine.search("crime AND drama", mode="boolean")

# Documents containing either term
results = engine.search("comedy OR horror", mode="boolean")

# Documents containing one term but not another
results = engine.search("action AND NOT comedy", mode="boolean")

# Grouping with parentheses
results = engine.search("(crime OR drama) AND NOT comedy", mode="boolean")
```

---

### 4. Ranked search — BM25

BM25 is the recommended ranking mode. It scores documents by relevance, rewards rare
terms, and normalizes for document length. Use `top_k` to limit how many results come back.

```python
results = engine.search("bank regulation financial market", mode="bm25", top_k=5)

for doc in results:
    print(f"[{doc['rank']}] score={doc['score']:.4f} | {doc['title']}")
```

Each ranked result includes two extra fields:
- `score` — relevance score (higher is better)
- `rank` — position in the result list starting from 1

---

### 5. Ranked search — TF-IDF

TF-IDF is a simpler scoring baseline. Useful as a reference to compare against BM25.

```python
results = engine.search("immune system lymph nodes", mode="tfidf", top_k=5)

for doc in results:
    print(f"[{doc['rank']}] score={doc['score']:.4f} | {doc['title']}")
```

---

### 6. Auto mode

Auto mode detects whether a query contains boolean operators and routes accordingly.
Queries with `AND`, `OR`, `NOT`, `(`, or `)` are treated as boolean. All others are keyword.

```python
results = engine.search("apple AND banana", mode="auto")  # routes to boolean
results = engine.search("dark knight",      mode="auto")  # routes to keyword
```

---

### 7. top_k

`top_k` limits the number of results returned. It applies to `bm25` and `tfidf` modes.

```python
results = engine.search("machine learning", mode="bm25", top_k=10)
```

`top_k` must be a positive integer. Passing `0` or a negative number raises a `ValueError`.

---

### 8. Using your own dataset

Any JSON file works as long as it contains a list of documents.

```python
engine = SearchEngine()
engine.build_index(
    doc_path="path/to/your_dataset.json",
    data_key="docs",    # change to match your JSON structure
    doc_id_key="id",
    exclude_doc_keys=["id"],
)

results = engine.search("your query here", mode="bm25", top_k=10)
```

Expected dataset shape:

```json
{
  "docs": [
    { "id": "1", "title": "First Document", "text": "..." },
    { "id": "2", "title": "Second Document", "text": "..." }
  ]
}
```

A flat list at the top level also works — just omit `data_key`:

```json
[
  { "id": "1", "title": "First Document", "text": "..." }
]
```

```python
engine.build_index(doc_path="path/to/flat.json", doc_id_key="id")
```

---

### 9. Using the Indexer directly

`SearchEngine` is a facade over `Indexer`. You can use `Indexer` directly for lower-level access.

```python
from recall_engine.search_engine import Indexer

indexer = Indexer()
indexer.load_or_build("datasets/movies.json", dataKey="movies", docIdKey="id")

# Raw keyword lookup
results = indexer.get_documents("action hero", operation="OR")

# Inspect the raw inverted index
index = indexer.get_index()            # dict[term -> list[doc_id]]
doc_map = indexer.get_doc_map()        # dict[doc_id -> document]
tf = indexer.get_term_frequencies()    # dict[term -> dict[doc_id -> count]]
df = indexer.get_document_frequencies()# dict[term -> int]
```

---

## Search Mode Reference

| Mode      | Description                                       | Supports `top_k` |
|-----------|---------------------------------------------------|------------------|
| `keyword` | Union of matched terms, sorted by doc ID          | No               |
| `boolean` | AND / OR / NOT operators, sorted by doc ID        | No               |
| `bm25`    | Ranked by BM25 score                              | Yes              |
| `tfidf`   | Ranked by TF-IDF score                            | Yes              |
| `auto`    | Detects boolean operators, falls back to keyword  | No               |

---

## Running Tests

```bash
# Full suite
poetry run pytest -v

# Toolkit behavior tests
poetry run pytest tests/test_search_engine_toolkit.py -v

# Performance and real-world dataset tests
poetry run pytest tests/test_search_engine_performance.py -v -s

# Coverage report
poetry run pytest --cov=recall_engine --cov-report=term-missing
```
