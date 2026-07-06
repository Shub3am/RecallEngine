import pytest
from fastapi.testclient import TestClient

from recall_engine.api import create_app
from recall_engine.search_engine import SearchEngine

#Test Command: uv run pytest tests/test_api.py -v


@pytest.fixture
def api_client() -> TestClient:
    engine = SearchEngine.from_documents(
        [
            {"id": "1", "title": "Red Apple", "overview": "fresh fruit"},
            {"id": "2", "title": "Green Banana", "overview": "tropical fruit"},
            {"id": "3", "title": "Apple Banana Smoothie", "overview": "sweet drink"},
        ]
    )
    return TestClient(create_app(engine))


def test_health_reports_document_count(api_client: TestClient):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "documents": 3}


def test_search_returns_ranked_results(api_client: TestClient):
    response = api_client.post("/search", json={"query": "banana", "mode": "bm25", "top_k": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "banana"
    assert body["mode"] == "bm25"
    assert body["count"] == 1
    assert body["results"][0]["id"] == "2"
    assert body["results"][0]["rank"] == 1


def test_search_defaults_to_auto_mode(api_client: TestClient):
    response = api_client.post("/search", json={"query": "apple AND banana"})

    assert [doc["id"] for doc in response.json()["results"]] == ["3"]


def test_invalid_mode_returns_400(api_client: TestClient):
    response = api_client.post("/search", json={"query": "apple", "mode": "neural"})

    assert response.status_code == 400
    assert "mode must be one of" in response.json()["detail"]


def test_malformed_boolean_query_returns_400(api_client: TestClient):
    response = api_client.post("/search", json={"query": "(apple AND banana", "mode": "boolean"})

    assert response.status_code == 400
    assert "Unmatched" in response.json()["detail"]


def test_missing_query_returns_422(api_client: TestClient):
    assert api_client.post("/search", json={"mode": "bm25"}).status_code == 422
