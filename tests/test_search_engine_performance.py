import json
import time
from pathlib import Path

import pytest

from recall_engine.search_engine import Indexer, SearchEngine


def _make_doc(doc_id: int) -> dict[str, str]:
    topic = "apple" if doc_id % 2 == 0 else "banana"
    sentiment = "comedy" if doc_id % 5 == 0 else "drama"
    title = f"Document {doc_id} {topic} {sentiment}"
    overview = " ".join(
        [
            "search",
            "engine",
            "performance",
            topic,
            sentiment,
            "token",
            "query",
            "index",
        ]
        * 8
    )
    return {"id": str(doc_id), "title": title, "overview": overview}


def _build_dataset(path: str, size: int = 2500) -> None:
    payload = {"docs": [_make_doc(i) for i in range(size)]}
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file)


def _build_real_world_sample(src_path: Path, dst_path: Path, size: int = 10000) -> None:
    with src_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    docs = payload.get("docs", []) if isinstance(payload, dict) else []
    sample = docs[:size]

    with dst_path.open("w", encoding="utf-8") as file:
        json.dump({"docs": sample}, file)


def test_search_engine_performance_baseline(tmp_path):
    dataset_path = tmp_path / "perf_docs.json"
    cache_path = tmp_path / "perf_cache.pkl"
    _build_dataset(str(dataset_path), size=2500)

    indexer = Indexer(file_path=str(cache_path))
    engine = SearchEngine(indexer=indexer)

    build_start = time.perf_counter()
    engine.build_index(
        doc_path=str(dataset_path),
        data_key="docs",
        doc_id_key="id",
        exclude_doc_keys=["id"],
        persist=False,
    )
    build_ms = (time.perf_counter() - build_start) * 1000

    keyword_start = time.perf_counter()
    keyword_results = engine.search("apple", mode="keyword")
    keyword_ms = (time.perf_counter() - keyword_start) * 1000

    boolean_start = time.perf_counter()
    boolean_results = engine.search("apple AND NOT comedy", mode="boolean")
    boolean_ms = (time.perf_counter() - boolean_start) * 1000

    print(f"build_ms={build_ms:.2f}")
    print(f"keyword_ms={keyword_ms:.2f}")
    print(f"boolean_ms={boolean_ms:.2f}")
    print(f"keyword_results={len(keyword_results)}")
    print(f"boolean_results={len(boolean_results)}")

    # Sanity checks for baseline stability and practical upper bounds.
    assert len(keyword_results) > 0
    assert len(boolean_results) > 0
    assert build_ms < 6000
    assert keyword_ms < 1000
    assert boolean_ms < 1500


@pytest.mark.slow
def test_search_engine_performance_real_world_sample(tmp_path):
    src_dataset = Path(__file__).resolve().parents[1] / "datasets" / "msmarco_passages.json"
    if not src_dataset.exists():
        pytest.skip("msmarco_passages.json not found in datasets/")

    dataset_path = tmp_path / "perf_docs_msmarco_sample.json"
    cache_path = tmp_path / "perf_cache_msmarco_sample.pkl"
    _build_real_world_sample(src_dataset, dataset_path, size=10000)

    indexer = Indexer(file_path=str(cache_path))
    engine = SearchEngine(indexer=indexer)

    build_start = time.perf_counter()
    engine.build_index(
        doc_path=str(dataset_path),
        data_key="docs",
        doc_id_key="id",
        exclude_doc_keys=["id"],
        persist=False,
    )
    build_ms = (time.perf_counter() - build_start) * 1000

    keyword_start = time.perf_counter()
    keyword_results = engine.search("bank regulation market", mode="keyword")
    keyword_ms = (time.perf_counter() - keyword_start) * 1000

    boolean_start = time.perf_counter()
    boolean_results = engine.search("bank AND NOT sports", mode="boolean")
    boolean_ms = (time.perf_counter() - boolean_start) * 1000

    print(f"real_world_build_ms={build_ms:.2f}")
    print(f"real_world_keyword_ms={keyword_ms:.2f}")
    print(f"real_world_boolean_ms={boolean_ms:.2f}")
    print(f"real_world_keyword_results={len(keyword_results)}")
    print(f"real_world_boolean_results={len(boolean_results)}")

    # These are coarse guardrails for a realistic sample (10k docs), not hard SLA targets.
    assert build_ms < 25000
    assert keyword_ms < 3000
    assert boolean_ms < 4000
