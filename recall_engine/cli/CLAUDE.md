# cli

## Owns

The `recall_engine` console script: argument parsing, printing search results and answers, and starting uvicorn for `serve`.

## Must not know about

How indexing, ranking or the HTTP routes work. It builds an engine with `SearchEngine.from_source` and hands it to `search`, `ask` or `create_app`.

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

## Called by

Users on the command line.
