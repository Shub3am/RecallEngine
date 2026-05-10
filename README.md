# RecallEngine

RecallEngine is a lightweight search toolkit for JSON datasets.

It currently provides:
- Text normalization (lowercase, punctuation removal, tokenization, stop-word filtering, stemming)
- Inverted-index based keyword retrieval
- Boolean query evaluation in the library API
- CLI entrypoint for dataset search
- Test coverage for toolkit behavior and baseline performance

## Vision

RecallEngine is intended to grow from a local keyword search toolkit into a modular retrieval platform for production RAG and search workloads.

The long-term vision is to provide a single, composable engine where developers can ingest data, index it with multiple strategies, retrieve relevant context with robust ranking, and expose the system through clean APIs and operational tooling.

## Status

Version: 0.1.0 (active development)

Core indexing and boolean query flow are implemented. Ranking algorithms such as BM25 and TF-IDF are planned next.

## Requirements

- Python >= 3.12
- Poetry

## Install

```bash
git clone https://github.com/Shub3am/RecallEngine
cd RecallEngine
poetry install --with dev
```

## Quick Start

Run the CLI against the bundled movie dataset:

```bash
poetry run recall_engine search "action hero"
```

Equivalent module invocation:

```bash
poetry run python -m recall_engine search "action hero"
```

## Library Usage

```python
from recall_engine.search_engine import SearchEngine

engine = SearchEngine()
engine.load_or_build_index(
    doc_path="datasets/movies.json",
    data_key="movies",
    doc_id_key="id",
    exclude_doc_keys=["id"],
)

# Auto mode picks keyword vs boolean behavior based on operators.
results = engine.search("apple AND NOT banana", mode="auto")
print(results[:3])
```

## Project Structure

```text
RecallEngine/
├── datasets/
│   ├── load_dataset.py
│   ├── movies.json
│   └── msmarco_passages.json
├── recall_engine/
│   ├── __main__.py
│   ├── cache/
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py
│   └── search_engine/
│       ├── __init__.py
│       ├── engine.py
│       ├── evaluator.py
│       ├── indexer.py
│       ├── lexer.py
│       ├── misc.py
│       ├── parser.py
│       ├── tokenizer.py
│       ├── utils.py
│       └── stop_words.txt
├── tests/
│   ├── test_search_engine_performance.py
│   └── test_search_engine_toolkit.py
├── DEVELOPER_GUIDE.md
├── pyproject.toml
└── README.md
```

## Testing

```bash
# All tests
poetry run pytest -v

# Toolkit tests
poetry run pytest tests/test_search_engine_toolkit.py -v

# Performance baseline test
poetry run pytest tests/test_search_engine_performance.py -v -s

# Coverage
poetry run pytest --cov=recall_engine --cov-report=term-missing
```

## Roadmap

- Add BM25 scoring
- Add TF-IDF scoring
- Expose search mode controls in CLI
- Add more datasets and ingestion connectors
- Add CI checks for performance regression thresholds

## Future of the Library

RecallEngine is expected to evolve into a layered system with:
- Pluggable retrieval modes: keyword, boolean, semantic, and hybrid
- Better ranking: BM25, TF-IDF, and learning-to-rank ready interfaces
- Ingestion connectors: files, APIs, and database sources
- Persistence options: local cache first, then backend adapters
- Service layer: API endpoints and deployment-ready interfaces
- Observability hooks: latency metrics, quality evaluation, and traceable query flow

The target outcome is a library that starts simple for local experimentation and scales to production retrieval stacks without forcing a rewrite.

## Contributing

1. Create a feature branch.
2. Add or update tests with your changes.
3. Run `poetry run pytest`.
4. Open a pull request.

See `DEVELOPER_GUIDE.md` for development conventions.
