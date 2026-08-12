# RecallEngine Developer Guide

## Setup

Requires Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Shub3am/RecallEngine
cd RecallEngine
uv sync --extra dev
```

## Run

```bash
uv run recall_engine search "action hero" --dataset datasets/movies.json --data-key movies
uv run recall_engine serve --dataset datasets/movies.json --data-key movies
```

## Test

```bash
# What CI runs on every push and pull request (Python 3.12, 3.13, 3.14)
uv run pytest -m "not slow"

# Everything, including the real embedding model and the MS MARCO benchmark
uv run pytest -v -s

# Coverage
uv run pytest --cov=recall_engine --cov-report=term-missing
```

Slow tests download the fastembed model (about 70 MB) and need `datasets/msmarco_passages.json`, which `datasets/load_dataset.py` produces.

## Architecture

```text
recall_engine/
├── __init__.py            # exports SearchEngine, the one import users need
├── __main__.py            # python -m recall_engine
├── cli/main.py            # recall_engine console script
├── api/app.py             # FastAPI app around a ready engine (api extra)
└── search_engine/
    ├── engine.py              # SearchEngine facade and mode routing
    ├── indexer.py             # inverted index, statistics, cache load/save
    ├── tokenizer.py           # normalization pipeline
    ├── lexer.py, parser.py    # boolean query to AST
    ├── evaluator.py           # AST to doc ids
    ├── ranked_retrieval.py    # BM25 and TF-IDF
    ├── semantic_retrieval.py  # embeddings and cosine ranking (semantic extra)
    ├── misc.py                # default dataset path
    └── utils.py               # AST node types
```

Each module folder has a `CLAUDE.md` with what it owns, what it must not know about, and its invariants.

Dependency direction is `cli` and `api` → `search_engine`. The core never imports `api`, `cli`, numpy or fastembed at module level, so `pip install recall-engine` without extras stays small.

## Conventions

- Absolute imports from `recall_engine`.
- New behavior lands with a test. Tests that download models or need large datasets are marked `@pytest.mark.slow`.
- Optional dependencies are imported lazily and fail with an `ImportError` that names the extra to install.
- Bump `Indexer` cache `version` whenever the pickled layout changes; old caches are then rebuilt instead of misread.

## Dependencies

```bash
uv add <package>                      # runtime
uv add --optional semantic <package>  # an extra
uv add --optional dev <package>       # development only
uv lock --upgrade                     # upgrade within constraints
```

Commit `uv.lock` with the change; CI installs with `uv sync --locked`.
