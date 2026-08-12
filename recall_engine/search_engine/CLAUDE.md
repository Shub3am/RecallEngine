# search_engine

## Owns

Turning documents into an inverted index with ranking statistics, caching that index on disk, and answering queries in every mode (`auto`, `keyword`, `boolean`, `bm25`, `tfidf`, `semantic`, `hybrid`). `SearchEngine` in `engine.py` is the only entry point users should need.

## Must not know about

HTTP, FastAPI, argparse or anything in `api/` and `cli/`. Retrieval code must not know where caches live; `engine.py` passes paths and cache keys in.

## Entry points

- `SearchEngine.from_json(path, ...)`: build or load a cached index from a JSON file.
- `SearchEngine.from_documents(docs, ...)`: in-memory index, never touches disk.
- `SearchEngine.search(query, mode, top_k)`: raises `ValueError` for a bad mode, a non-positive `top_k` or a malformed boolean query. Callers map that to user errors.

## Invariants and gotchas

- The index cache defaults to `~/.cache/recall_engine/index.pkl`. It is reused only when the source fingerprint (path, size, mtime, data key, id key, excluded keys) matches; otherwise it is rebuilt. Bump the pickle `version` in `Indexer.save` when its layout changes.
- The cache is a pickle. Only load caches this library wrote; never point `cache_path` at an untrusted file.
- `semantic_retrieval.py` is imported lazily from `engine.py`. Importing it at module level breaks installs without the `semantic` extra.
- Semantic retrieval is built once per engine behind a lock, because the API calls `search` from a threadpool. Rebuilding or reloading the index resets it.
- Embeddings are cached at `<index path>.embeddings.npz` only for file-built indexes, keyed by source fingerprint plus model name.
- Hybrid fuses the top `HYBRID_CANDIDATE_POOL` (100) of BM25 and semantic with RRF, `RRF_K = 60`. Its `score` is only comparable within one query.
- Doc ids are stored as strings, whatever type the JSON had.
- `Indexer` still takes camelCase keyword arguments (`docPath`, `dataKey`); `SearchEngine` exposes snake_case and translates.

## Called by

`recall_engine/__init__.py`, `recall_engine/api/app.py`, `recall_engine/cli/main.py` and the tests.
