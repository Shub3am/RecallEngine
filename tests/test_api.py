from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient

from recall_engine.api import create_app
from recall_engine.search_engine import SearchEngine

#Test Command: uv run pytest tests/test_api.py -v


def _engine() -> SearchEngine:
    return SearchEngine.from_documents(
        [
            {"id": "1", "title": "Red Apple", "overview": "fresh fruit"},
            {"id": "2", "title": "Green Banana", "overview": "tropical fruit"},
            {"id": "3", "title": "Apple Banana Smoothie", "overview": "sweet drink"},
        ]
    )


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(create_app(_engine()))


@pytest.fixture
def api_client_with_key() -> TestClient:
    return TestClient(create_app(_engine(), api_key="test-secret"))


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


def test_search_without_api_key_returns_401_when_key_is_configured(api_client_with_key: TestClient):
    assert api_client_with_key.post("/search", json={"query": "apple"}).status_code == 401


def test_search_with_wrong_api_key_returns_401(api_client_with_key: TestClient):
    response = api_client_with_key.post("/search", json={"query": "apple"}, headers={"X-API-Key": "wrong"})

    assert response.status_code == 401


def test_search_with_correct_api_key_succeeds(api_client_with_key: TestClient):
    response = api_client_with_key.post("/search", json={"query": "apple"}, headers={"X-API-Key": "test-secret"})

    assert response.status_code == 200


def test_health_stays_open_when_api_key_is_configured(api_client_with_key: TestClient):
    assert api_client_with_key.get("/health").status_code == 200


def test_ask_returns_answer_with_citations(api_client: TestClient, monkeypatch):
    def fake_answer_question(question, passages, client=None):
        return {
            "question": question,
            "answer": "Banana.[1]",
            "citations": [{"number": 1, "passage_id": passages[0][0], "cited_text": "Green Banana"}],
        }

    monkeypatch.setattr("recall_engine.rag.answer_question", fake_answer_question)

    response = api_client.post("/ask", json={"question": "which fruit is tropical"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Banana.[1]"
    assert response.json()["citations"][0]["passage_id"] == "2"


def test_ask_with_no_matching_documents_returns_400(api_client: TestClient):
    response = api_client.post("/ask", json={"question": "spaceship"})

    assert response.status_code == 400


def test_ask_requires_api_key_when_configured(api_client_with_key: TestClient):
    response = api_client_with_key.post("/ask", json={"question": "banana"})

    assert response.status_code == 401


def test_openapi_reports_the_package_version():
    client = TestClient(create_app(_engine()))

    assert client.get("/openapi.json").json()["info"]["version"] == version("recall-engine")


def test_retrieve_returns_passages_with_their_text(api_client: TestClient):
    response = api_client.post("/retrieve", json={"query": "banana", "top_k": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "bm25"
    assert body["count"] == 1
    assert body["passages"][0]["id"] == "2"
    assert body["passages"][0]["rank"] == 1
    assert "Green Banana" in body["passages"][0]["text"]
    assert body["passages"][0]["document"]["title"] == "Green Banana"


def test_retrieve_rejects_unranked_mode(api_client: TestClient):
    response = api_client.post("/retrieve", json={"query": "banana", "mode": "keyword"})

    assert response.status_code == 400


def test_retrieve_requires_the_api_key(api_client_with_key: TestClient):
    response = api_client_with_key.post("/retrieve", json={"query": "banana"})

    assert response.status_code == 401
