# cli

## Owns

The `recall_engine` console script: argument parsing, printing results, passages and answers, and starting uvicorn for `serve`.

## Must not know about

How indexing, ranking or the HTTP routes work. It opens an engine with `SearchEngine.from_source` or `SearchEngine.from_index` and hands it to `search`, `retrieve`, `ask` or `create_app`. `ingest` builds one with `from_source` and saves it.

## Entry points

- `cli()`: the `[project.scripts]` target, also run by `python -m recall_engine`.

## Invariants and gotchas

- Mode choices and `ask` defaults come from `SEARCH_MODES`, `RETRIEVAL_MODES` and `DEFAULT_RETRIEVAL_*` in `search_engine/engine.py`; do not hardcode them here.
- `serve` reads the API key from the `RECALL_ENGINE_API_KEY` environment variable, never a flag, so it does not show up in `ps`.
- `serve` binds to `127.0.0.1` by default. Exposing it needs `--host 0.0.0.0`.
- The SQL flag is `--sql`, not `--query`, because the `search` subcommand already uses `query` for the search text.
- `--data-key` defaults to empty, which lets a JSON file with exactly one top-level list work without it.
- The default `--dataset` is the relative path `./datasets/movies.json`, which only exists when run from the repo root.
- `recall_engine.api` and uvicorn are imported inside `_serve` so `search` works without the `api` extra.
- `cli()` turns any `ImportError` into `Error: <message>` on stderr and exit code 1, because every optional extra raises one naming its install command. An `ImportError` from a real bug is shown the same way, without a traceback.
- `--dataset` and `--index` are mutually exclusive. With `--index`, `--data-key`, `--table` and `--sql` are ignored because the saved index already holds the passages.
- `ingest` calls `indexer.save()` itself only when there is no fingerprint, because `from_source` already saved file-backed sources and never writes one for database URLs. A saved URL snapshot has no fingerprint, so its embeddings cannot be cached and `ingest` skips `--embed` for it.

## Called by

Users on the command line.
