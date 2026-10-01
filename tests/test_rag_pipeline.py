from pathlib import Path

import pytest

from recall_engine import SearchEngine
from tests.test_semantic_search import ConceptEmbeddingModel

#Test Command: uv run pytest tests/test_rag_pipeline.py -v


def write_folder(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for file_name, text in files.items():
        (root / file_name).write_text(text, encoding="utf-8")
    return root


@pytest.fixture
def two_folders(tmp_path: Path) -> list[str]:
    policies = write_folder(tmp_path / "policies", {"refunds.md": "Refunds are paid within 14 days."})
    support = write_folder(tmp_path / "support", {"faq.md": "Reset your password from the login page."})
    return [str(policies), str(support)]


def test_from_source_ingests_several_sources_into_one_index(two_folders: list[str], tmp_path: Path):
    engine = SearchEngine.from_source(two_folders, cache_path=str(tmp_path / "index.pkl"))

    assert sorted(engine.indexer.get_doc_map()) == ["faq.md#1", "refunds.md#1"]
    assert [doc["passage_id"] for doc in engine.search("password", mode="bm25")] == ["faq.md#1"]


def test_several_sources_reuse_the_cache_until_one_changes(two_folders: list[str], tmp_path: Path):
    cache_path = str(tmp_path / "index.pkl")
    SearchEngine.from_source(two_folders, cache_path=cache_path)
    (Path(two_folders[1]) / "billing.md").write_text("Invoices are sent monthly.", encoding="utf-8")

    reloaded = SearchEngine.from_source(two_folders, cache_path=cache_path)

    assert "billing.md#1" in reloaded.indexer.get_doc_map()


def test_sources_that_produce_the_same_passage_id_are_rejected(tmp_path: Path):
    first = write_folder(tmp_path / "first", {"notes.md": "alpha"})
    second = write_folder(tmp_path / "second", {"notes.md": "beta"})

    with pytest.raises(ValueError, match="notes.md#1"):
        SearchEngine.from_source([str(first), str(second)], cache_path=str(tmp_path / "index.pkl"))


def test_embed_caches_vectors_so_a_reopened_index_skips_embedding(two_folders: list[str], tmp_path: Path):
    cache_path = str(tmp_path / "index.pkl")
    ingesting_engine = SearchEngine.from_source(two_folders, cache_path=cache_path, embedding_model=ConceptEmbeddingModel())

    assert ingesting_engine.embed() == 2
    assert (tmp_path / "index.embeddings.npz").exists()

    reopening_model = ConceptEmbeddingModel()
    reopened = SearchEngine.from_index(cache_path, embedding_model=reopening_model)
    results = reopened.search("refunds", mode="hybrid", top_k=1)

    assert [doc["passage_id"] for doc in results] == ["refunds.md#1"]
    assert reopening_model.embedded_passage_count == 0


def test_embedding_model_can_be_chosen_by_name(monkeypatch):
    loaded_model_names = []

    def fake_load_embedding_model(model_name):
        loaded_model_names.append(model_name)
        return ConceptEmbeddingModel()

    monkeypatch.setattr(
        "recall_engine.search_engine.semantic_retrieval.load_embedding_model", fake_load_embedding_model
    )
    engine = SearchEngine.from_documents([{"id": "1", "text": "ocean"}], embedding_model="BAAI/bge-base-en-v1.5")

    assert engine.embed() == 1
    assert loaded_model_names == ["BAAI/bge-base-en-v1.5"]
