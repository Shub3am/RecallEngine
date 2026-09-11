# RecallEngine

Search library for JSON documents: keyword, boolean, BM25, TF-IDF, semantic and hybrid, from one import.

## Modules

- `recall_engine/search_engine/`: indexing, query parsing and every retrieval mode. See `recall_engine/search_engine/CLAUDE.md`.
- `recall_engine/api/`: FastAPI app that serves a ready engine over HTTP (`api` extra). See `recall_engine/api/CLAUDE.md`.
- `recall_engine/cli/`: the `recall_engine` console script (`search`, `serve`). See `recall_engine/cli/CLAUDE.md`.
- `tests/`: pytest suite; `slow` marks tests that download a model or need large datasets.
- `datasets/`: sample data (`movies.json`) and the MS MARCO loader used by the benchmark.

## Run, test, deploy

```bash
uv sync --extra dev
uv run recall_engine search "query" --dataset datasets/movies.json --data-key movies
uv run pytest -m "not slow"     # what CI runs
uv run pytest -v -s             # everything, including slow tests
```

CI: `.github/workflows/tests.yml` runs the fast suite on Python 3.12, 3.13 and 3.14. There is no deploy pipeline; users install from git (`pip install "recall-engine[all] @ git+https://github.com/Shub3am/RecallEngine"`).

## Repo-wide rules

- Dependencies go through uv and `pyproject.toml`; commit `uv.lock` with them (CI uses `--locked`).
- The core never imports numpy, fastembed, fastapi or uvicorn at module level. Optional dependencies load lazily and raise an `ImportError` naming the extra.
- `recall_engine/__init__.py` exports only `SearchEngine`; that is the one-import promise.
- No em dashes in code, docs or commit messages.
