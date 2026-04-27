# RecallEngine Developer Guide

## Overview

RecallEngine is a Python search toolkit built around an inverted index and normalization pipeline.

Current capabilities:
- Keyword retrieval
- Boolean retrieval (library API)
- JSON dataset indexing
- Persistent cache file for index/doc map

Main package surface:
- `recall_engine.search_engine.SearchEngine`
- `recall_engine.search_engine.Indexer`

## Vision

RecallEngine is being developed toward a complete retrieval foundation for modern AI and search applications.

The goal is to keep the core developer experience simple while expanding capabilities so the same library can support both local prototypes and production retrieval systems.

## Requirements

- Python >= 3.12
- Poetry

## Setup

```bash
git clone https://github.com/Shub3am/RecallEngine
cd RecallEngine
poetry install --with dev
```

## Run CLI

```bash
poetry run recall_engine search "your query"
```

Alternative entrypoint:

```bash
poetry run python -m recall_engine search "your query"
```

Notes:
- Current CLI command is `search` with a single positional `query` argument.
- CLI currently uses keyword retrieval via the indexer flow.

## Run Tests

```bash
# Entire suite
poetry run pytest -v

# Toolkit behavior tests
poetry run pytest tests/test_search_engine_toolkit.py -v

# Performance baseline test
poetry run pytest tests/test_search_engine_performance.py -v -s

# Coverage
poetry run pytest --cov=recall_engine --cov-report=term-missing
```

## High-Level Architecture

```text
recall_engine/
├── __main__.py                     # Module entrypoint
├── cli/main.py                     # Console script target (recall_engine)
└── search_engine/
    ├── engine.py                   # SearchEngine facade
    ├── indexer.py                  # Inverted index + cache load/save
    ├── lexer.py                    # Query lexer for boolean syntax
    ├── parser.py                   # AST parser
    ├── evaluator.py                # Boolean AST evaluator
    ├── tokenizer.py                # Normalization/tokenization pipeline
    ├── misc.py                     # Paths and dataset helpers
    └── utils.py                    # Shared AST node utilities
```

## Development Conventions

- Use absolute imports from `recall_engine`.
- Keep public behavior covered by tests before refactors.
- Preserve backward-compatible parameter names where already used by tests.
- Use `poetry run` for all commands to ensure the project environment is active.

## Dependency Management

```bash
# Runtime dependency
poetry add <package>

# Dev dependency
poetry add --group dev <package>

# Upgrade dependencies
poetry update

# Check outdated dependencies
poetry show --outdated
```

## Next Suggested Work

- Implement BM25 scoring in the search layer.
- Add ranking mode selection in library and CLI.
- Add malformed query and index corruption edge-case tests.

## Future Direction

Planned evolution of the library:
- Retrieval depth: keyword and boolean today, semantic and hybrid retrieval next
- Ranking quality: BM25 and TF-IDF first, then extensible ranking interfaces
- Data ingestion: broader connectors beyond local JSON datasets
- Runtime surfaces: stable Python API and optional service/API layer
- Production readiness: persistence backends, performance instrumentation, and evaluation tooling

Target state:
- A modular retrieval engine for RAG pipelines where ingestion, indexing, retrieval, and ranking are separable components that can be combined based on workload.
