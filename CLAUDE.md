# RecallEngine

Search and RAG library for files, folders and databases: keyword, boolean, BM25, TF-IDF, semantic and hybrid search, plus cited answers from Claude, from one import.

## Modules

- `recall_engine/search_engine/`: indexing, query parsing and every retrieval mode. See `recall_engine/search_engine/CLAUDE.md`.
- `recall_engine/sources/`: turns files, folders and databases into documents (`formats`, `database` extras). See `recall_engine/sources/CLAUDE.md`.
- `recall_engine/rag/`: answers a question from retrieved passages with Claude, with citations (`rag` extra). See `recall_engine/rag/CLAUDE.md`.
- `recall_engine/api/`: FastAPI app that serves a ready engine over HTTP (`api` extra). See `recall_engine/api/CLAUDE.md`.
- `recall_engine/cli/`: the `recall_engine` console script (`ingest`, `search`, `retrieve`, `ask`, `serve`). See `recall_engine/cli/CLAUDE.md`.
- `tests/`: pytest suite; `slow` marks tests that download a model or need large datasets.
- `datasets/`: sample data (`movies.json`) and the MS MARCO loader used by the benchmark.

## Run, test, deploy

```bash
uv sync --extra dev
uv run recall_engine search "query" --dataset datasets/movies.json
uv run recall_engine ask "question" --dataset ./docs   # needs ANTHROPIC_API_KEY
uv run recall_engine ingest ./docs --index kb.pkl --embed && uv run recall_engine retrieve "query" --index kb.pkl
uv run pytest -m "not slow"     # what CI runs
uv run pytest -v -s             # everything, including slow tests
```

CI: `.github/workflows/tests.yml` runs the fast suite on Python 3.12, 3.13 and 3.14.

Release: push a `v*` tag matching `pyproject.toml`'s version. `.github/workflows/release.yml` attaches the wheel and sdist to a GitHub Release and pushes the `Dockerfile` image (amd64, arm64) to `ghcr.io/shub3am/recallengine`.

## Repo-wide rules

- Dependencies go through uv and `pyproject.toml`; commit `uv.lock` with them (CI uses `--locked`).
- The core never imports numpy, fastembed, fastapi, uvicorn, pypdf, python-docx, openpyxl, sqlalchemy or anthropic at module level. Optional dependencies load lazily and raise an `ImportError` naming the extra.
- `recall_engine/__init__.py` exports only `SearchEngine`; that is the one-import promise.
- No em dashes in code, docs or commit messages.
