import json
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

from recall_engine.search_engine import Indexer, SearchEngine

#Test Command: uv run pytest tests/test_semantic_search.py -v

_CONCEPTS = {
    "space": 0, "stars": 0, "galaxy": 0, "astronaut": 0,
    "ocean": 1, "sea": 1, "water": 1, "sailor": 1,
    "kitchen": 2, "recipe": 2, "chef": 2, "baking": 2,
}


class ConceptEmbeddingModel:
    """Tiny stand-in for a real embedding model: words that share a concept share a dimension."""

    def __init__(self) -> None:
        self.embedded_passage_count = 0

    def _embed(self, text: str) -> np.ndarray:
        vector = np.zeros(3)
        for word in text.lower().split():
            if word in _CONCEPTS:
                vector[_CONCEPTS[word]] += 1
        return vector

    def passage_embed(self, texts):
        for text in texts:
            self.embedded_passage_count += 1
            yield self._embed(text)

    def query_embed(self, query):
        yield self._embed(query)


_DOCUMENTS = [
    {"id": "1", "title": "Stars Above", "overview": "an astronaut drifts through space"},
    {"id": "2", "title": "Deep Blue", "overview": "a sailor lost at sea"},
    {"id": "3", "title": "Sunday Kitchen", "overview": "a chef shares a baking recipe"},
    {"id": "4", "title": "Galaxy Galaxy", "overview": "galaxy galaxy galaxy"},
]


def _ids(results: list[dict]) -> list[str]:
    return [str(doc["id"]) for doc in results]


@pytest.fixture
def semantic_engine() -> SearchEngine:
    return SearchEngine.from_documents(_DOCUMENTS, embedding_model=ConceptEmbeddingModel())


def test_semantic_search_matches_meaning_without_shared_words(semantic_engine: SearchEngine):
    results = semantic_engine.search("ocean water", mode="semantic", top_k=1)

    assert _ids(results) == ["2"]
    assert results[0]["rank"] == 1
    assert results[0]["score"] == pytest.approx(1.0)


def test_keyword_modes_miss_what_semantic_finds(semantic_engine: SearchEngine):
    assert semantic_engine.search("ocean water", mode="bm25") == []


def test_hybrid_search_fuses_keyword_and_semantic_rankings(semantic_engine: SearchEngine):
    results = semantic_engine.search("galaxy astronaut", mode="hybrid", top_k=2)

    assert set(_ids(results)) == {"1", "4"}
    assert [doc["rank"] for doc in results] == [1, 2]
    assert results[0]["score"] >= results[1]["score"]


def test_hybrid_returns_semantic_matches_with_no_keyword_hits(semantic_engine: SearchEngine):
    results = semantic_engine.search("recipe", mode="hybrid", top_k=1)

    assert _ids(results) == ["3"]


class SlowConceptEmbeddingModel(ConceptEmbeddingModel):
    def passage_embed(self, texts):
        time.sleep(0.2)
        yield from super().passage_embed(texts)


def test_concurrent_first_semantic_searches_embed_documents_once():
    embedding_model = SlowConceptEmbeddingModel()
    engine = SearchEngine.from_documents(_DOCUMENTS, embedding_model=embedding_model)

    with ThreadPoolExecutor(max_workers=8) as pool:
        result_ids = list(pool.map(lambda _: _ids(engine.search("sailor", mode="semantic", top_k=1)), range(8)))

    assert result_ids == [["2"]] * 8
    assert embedding_model.embedded_passage_count == len(_DOCUMENTS)


def test_semantic_embeddings_are_cached_next_to_the_index(tmp_path):
    dataset_path = tmp_path / "docs.json"
    dataset_path.write_text(json.dumps({"docs": _DOCUMENTS}), encoding="utf-8")
    cache_path = str(tmp_path / "index.pkl")

    first_model = ConceptEmbeddingModel()
    SearchEngine.from_json(str(dataset_path), data_key="docs", cache_path=cache_path, embedding_model=first_model).search(
        "sea", mode="semantic"
    )
    second_model = ConceptEmbeddingModel()
    cached_results = SearchEngine.from_json(
        str(dataset_path), data_key="docs", cache_path=cache_path, embedding_model=second_model
    ).search("sea", mode="semantic", top_k=1)

    assert first_model.embedded_passage_count == len(_DOCUMENTS)
    assert second_model.embedded_passage_count == 0
    assert _ids(cached_results) == ["2"]


def test_semantic_mode_explains_missing_extra(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def import_without_fastembed(name, *args, **kwargs):
        if name == "fastembed":
            raise ImportError("No module named 'fastembed'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_fastembed)
    engine = SearchEngine(indexer=Indexer())
    engine.indexer.build_from_documents(_DOCUMENTS)

    with pytest.raises(ImportError, match=r"recall-engine\[semantic\]"):
        engine.search("sea", mode="semantic")


@pytest.mark.slow
def test_semantic_search_with_real_fastembed_model():
    pytest.importorskip("fastembed")
    engine = SearchEngine.from_documents(
        [
            {"id": "1", "text": "The astronaut floated outside the space station."},
            {"id": "2", "text": "Grandma baked bread in her kitchen every Sunday."},
        ]
    )

    results = engine.search("cosmonaut orbiting earth", mode="semantic", top_k=1)

    assert _ids(results) == ["1"]
