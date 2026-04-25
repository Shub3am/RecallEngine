import json

import pytest

from recall_engine.search_engine import Indexer, SearchEngine


@pytest.fixture
def sample_dataset_path(tmp_path: str) -> str:
    data = {
        "docs": [
            {"id": "1", "title": "Red Apple", "overview": "fresh fruit"},
            {"id": "2", "title": "Green Banana", "overview": "tropical fruit"},
            {"id": "3", "title": "Apple Banana Smoothie", "overview": "sweet drink"},
            {"id": "4", "title": "Comedy Night", "overview": "funny show"},
        ]
    }
    dataset_file = tmp_path or "dataset.json"
    with open(dataset_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return str(dataset_file)


@pytest.fixture
def engine(sample_dataset_path: str, tmp_path: str) -> SearchEngine:
    index_file = tmp_path or "cache.pkl"
    indexer = Indexer(file_path=str(index_file))
    search_engine = SearchEngine(indexer=indexer)
    search_engine.build_index(
        doc_path=str(sample_dataset_path),
        data_key="docs",
        doc_id_key="id",
        exclude_doc_keys=["id"],
        persist=False,
    )
    return search_engine


def _ids(results: list[dict[str, str]]) -> list[str]:
    return [str(doc["id"]) for doc in results]


def test_keyword_search_returns_expected_documents(engine: SearchEngine):
    results = engine.search("apple", mode="keyword")
    assert _ids(results) == ["1", "3"]


def test_boolean_and_search(engine: SearchEngine):
    results = engine.search("apple AND banana", mode="boolean")
    assert _ids(results) == ["3"]


def test_boolean_or_search(engine: SearchEngine):
    results = engine.search("apple OR banana", mode="boolean")
    assert _ids(results) == ["1", "2", "3"]


def test_boolean_not_search(engine: SearchEngine):
    results = engine.search("apple AND NOT banana", mode="boolean")
    assert _ids(results) == ["1"]


def test_operator_precedence_not_and_or(engine: SearchEngine):
    results = engine.search("apple OR banana AND smoothie", mode="boolean")
    assert _ids(results) == ["1", "3"]


def test_parentheses_override_precedence(engine: SearchEngine):
    results = engine.search("(apple OR banana) AND smoothie", mode="boolean")
    assert _ids(results) == ["3"]


def test_auto_mode_detects_boolean(engine: SearchEngine):
    results = engine.search("apple AND banana", mode="auto")
    assert _ids(results) == ["3"]


def test_invalid_mode_raises_value_error(engine: SearchEngine):
    with pytest.raises(ValueError, match="mode must be one of"):
        engine.search("apple", mode="bm25")
