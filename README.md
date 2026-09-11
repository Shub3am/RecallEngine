# RecallEngine

RecallEngine is a search library for JSON documents. You point it at a file, and one import gives you keyword, boolean, BM25, TF-IDF, semantic and hybrid search. You can also serve it over HTTP.

## Install

```bash
# Everything: keyword, ranked, semantic, hybrid and the HTTP API
pip install "recall-engine[all] @ git+https://github.com/Shub3am/RecallEngine"

# Keyword, boolean, BM25 and TF-IDF only (no numpy, no model download)
pip install "recall-engine @ git+https://github.com/Shub3am/RecallEngine"
```

| Extra      | Adds                                      |
|------------|-------------------------------------------|
| `semantic` | `semantic` and `hybrid` modes (fastembed) |
| `api`      | `recall_engine serve` and `create_app`    |
| `all`      | both of the above                         |

Requires Python 3.12 or newer.

## Quick start

```python
from recall_engine import SearchEngine

engine = SearchEngine.from_json("docs.json", data_key="docs")

engine.search("dark knight")                               # keyword
engine.search("crime AND NOT comedy")                      # boolean, picked automatically
engine.search("bank regulation", mode="bm25", top_k=5)     # ranked
engine.search("films about space travel", mode="semantic", top_k=5)
engine.search("space travel", mode="hybrid", top_k=5)      # BM25 + semantic, fused
```

Already have the documents in memory:

```python
engine = SearchEngine.from_documents([
    {"id": "1", "title": "Red Apple", "overview": "fresh fruit"},
    {"id": "2", "title": "Green Banana", "overview": "tropical fruit"},
])
```

`from_json` caches the built index in `~/.cache/recall_engine/`. It rebuilds automatically when the file or the indexing options change.

## CLI

```bash
recall_engine search "space travel" --dataset docs.json --data-key docs --mode hybrid --top-k 5
recall_engine serve --dataset docs.json --data-key docs --port 8000
```

## HTTP API

```bash
curl localhost:8000/health
# {"status":"ok","documents":2}

curl -X POST localhost:8000/search -H 'content-type: application/json' \
  -d '{"query": "banana", "mode": "bm25", "top_k": 1}'
# {"query":"banana","mode":"bm25","count":1,"results":[{"id":"2", ..., "score":0.69,"rank":1}]}
```

Invalid modes and malformed boolean queries return 400. Interactive docs are served at `/docs`.

To require a key, set `RECALL_ENGINE_API_KEY` before `recall_engine serve`. `/search` then answers 401 unless the request sends a matching `X-API-Key` header. `/health` stays open for load balancer probes. The server binds to `127.0.0.1` by default; pass `--host 0.0.0.0` to expose it, and put TLS in front of it (a reverse proxy or your load balancer).

To mount it in your own app, pass it an engine:

```python
from recall_engine.api import create_app

app = create_app(SearchEngine.from_json("docs.json", data_key="docs"), api_key="your-secret")
```

## Search modes

| Mode       | What it does                                              | `top_k` |
|------------|-----------------------------------------------------------|---------|
| `auto`     | `boolean` if the query has AND, OR, NOT or parentheses, otherwise `keyword` | No |
| `keyword`  | Documents containing any query term, sorted by id         | No      |
| `boolean`  | AND, OR, NOT and parentheses, sorted by id                | No      |
| `bm25`     | Ranked by BM25                                            | Yes     |
| `tfidf`    | Ranked by TF-IDF                                          | Yes     |
| `semantic` | Ranked by embedding similarity (`BAAI/bge-small-en-v1.5`) | Yes     |
| `hybrid`   | BM25 and semantic rankings merged with Reciprocal Rank Fusion | Yes |

Ranked results carry two extra fields: `score` and `rank`.

The first semantic search downloads the embedding model (about 70 MB) and embeds every document. For file-backed engines the embeddings are cached next to the index.

See [USAGE.md](USAGE.md) for the full guide and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) to work on the code.

## Status

Version 1.0.0.
