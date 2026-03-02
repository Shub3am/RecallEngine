# RecallEngine — Developer Guide

## Overview

RecallEngine is a keyword-based search engine over a movie dataset ( currently ). The core pipeline normalizes input text (lowercase → strip punctuation → tokenize → remove stop words → Porter stem) before matching against indexed titles.

---

## Requirements

- Python ≥ 3.12
- [Poetry](https://python-poetry.org/)

---

## Setup

```bash
git clone <"https://github.com/Shub3am/RecallEngine">
cd RecallEngine
poetry install --with dev
```

---

## Project Structure

```
RecallEngine/
├── pyproject.toml
├── poetry.lock
├── recall_engine/
│   ├── cli/
│   │   ├── keyword_search_cli.py   # Core pipeline: normalize, match, CLI entry
│   │   ├── misc.py                 # get_stop_words, dataset_loader
│   │   └── indexer.py
│   └── helper/
│       └── stop_words.txt
└── tests/
    ├── conftest.py
    ├── test_keyword_search_cli.py
    ├── test_misc.py
    └── test_integration.py
```

---

## Running the CLI

```bash
poetry run python recall_engine/cli/keyword_search_cli.py search "<query>"
```

---

## Testing

```bash
# Run all tests
poetry run pytest -v

# Run a specific module, class, or method
poetry run pytest tests/test_keyword_search_cli.py::TestTokensStemmer -v

# Filter by name
poetry run pytest -k "stemmer" -v

# With coverage
poetry run pytest --cov=recall_engine --cov-report=term-missing

# HTML coverage report
poetry run pytest --cov=recall_engine --cov-report=html
open htmlcov/index.html

# Watch mode
poetry run ptw -- -v
```

> Always invoke pytest via `poetry run` to ensure the project's virtualenv is active.

---

## Conventions

**Imports** — use absolute imports throughout:

```python
from recall_engine.cli.misc import get_stop_words, dataset_loader
```

**Mocking** — patch at the point of use, not the point of definition:

```python
@patch('recall_engine.cli.keyword_search_cli.get_stop_words')
def test_something(self, mock_stop_words): ...
```

---

## Dependencies

```bash
poetry add <package>                 # Runtime
poetry add --group dev <package>     # Development
poetry update                        # Update all
poetry show --outdated               # Check for updates
```

---
