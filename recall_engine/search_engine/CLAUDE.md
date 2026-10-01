# search_engine

## Owns

Turning documents into an inverted index with ranking statistics, caching that index on disk, and answering queries in every mode (`auto`, `keyword`, `boolean`, `bm25`, `tfidf`, `semantic`, `hybrid`). `ask` retrieves passages and hands them to `recall_engine.rag`. `SearchEngine` in `engine.py` is the only entry point users should need.

## Must not know about

HTTP, FastAPI, argparse or anything in `api/` and `cli/`. File formats and database drivers belong to `sources/`; the Claude call belongs to `rag/`. Retrieval code must not know where caches live; `engine.py` passes paths and cache keys in.

## Entry points

- `SearchEngine.from_json(path, ...)`: build or load a cached index from a JSON file.
- `SearchEngine.from_documents(docs, ...)`: in-memory index, never touches disk.
- `SearchEngine.from_source(source, ...)`: one source or a list of files, folders and database URLs through `recall_engine.sources`, merged into one index and cached like `from_json`. Raises `ValueError` when two sources produce the same passage id, because the indexer keys documents by it.
- `SearchEngine.from_index(index_path, embedding_model)`: opens a saved index without touching its sources. Raises `FileNotFoundError` when nothing was saved there.
- `SearchEngine.embed()`: embeds every passage up front and returns the count, so ingestion pays the embedding cost instead of the first query.
- `SearchEngine.retrieve(query, mode, top_k)`: the retrieval step of RAG. Returns `{rank, score, id, text, document}` per passage for any model's prompt. Ranked modes only (`RETRIEVAL_MODES`), because unranked modes ignore `top_k`; another mode raises `ValueError`.
- `SearchEngine.ask(question, mode, top_k)`: `retrieve` plus Claude. Raises `ValueError` when nothing matches, and anything `retrieve` or `answer_question` raises.
- `SearchEngine.search(query, mode, top_k)`: raises `ValueError` for a bad mode, a non-positive `top_k` or a malformed boolean query. Callers map that to user errors.

## Invariants and gotchas

- The index cache defaults to `~/.cache/recall_engine/index.pkl`. It is reused only when the source fingerprint (path, size, mtime, data key, id key, excluded keys) matches; otherwise it is rebuilt. Bump the pickle `version` in `Indexer.save` when its layout changes.
- The cache is a pickle. Only load caches this library wrote; never point `cache_path` at an untrusted file.
- A single source keeps its own fingerprint and a list is stored as `{"sources": [...]}`, so pre-1.2 caches stay valid.
- `from_source` caches only when every `sources.source_fingerprint` returns one; database URLs return `None`, so they are reloaded on every start and have no embeddings cache.
- `recall_engine.sources` and `recall_engine.rag` are imported inside `from_source` and `ask`, so core installs never load their extras.
- The indexer stores `doc_id_key` in the cache so `retrieve` can label passages by id. Caches written before 1.1 load it as `"id"`.
- `semantic_retrieval.py` is imported lazily from `engine.py`. Importing it at module level breaks installs without the `semantic` extra.
- `embedding_model` is a model object, a fastembed model name (loaded on first use) or `None` for `BAAI/bge-small-en-v1.5`. A reopened index must use the same model as ingestion, or the cached vectors miss and every passage is embedded again.
- `load_embedding_model` turns off onnxruntime telemetry before the model loads. With it on, macOS processes abort with exit code 134 at shutdown after a semantic or hybrid search. onnxruntime arrives through fastembed, not as a direct dependency.
- Semantic retrieval is built once per engine behind a lock, because the API calls `search` from a threadpool. Rebuilding or reloading the index resets it.
- Embeddings are cached at `<index path>.embeddings.npz` only for file-built indexes, keyed by source fingerprint plus model name.
- Hybrid fuses the top `HYBRID_CANDIDATE_POOL` (100) of BM25 and semantic with RRF, `RRF_K = 60`. Its `score` is only comparable within one query.
- Doc ids are stored as strings, whatever type the JSON had.
- `Indexer` still takes camelCase keyword arguments (`docPath`, `dataKey`); `SearchEngine` exposes snake_case and translates.

## Called by

`recall_engine/__init__.py`, `recall_engine/api/app.py`, `recall_engine/cli/main.py` and the tests.
