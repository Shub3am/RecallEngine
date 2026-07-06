"""Serves an already built SearchEngine over HTTP.

Must not build or load indexes, read files, or parse CLI arguments; the caller
hands it a ready engine so the same app works for any dataset.
"""
from typing import Any

MISSING_API_EXTRA = 'The HTTP API needs the optional extra: pip install "recall-engine[api]"'

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:
    raise ImportError(MISSING_API_EXTRA) from exc

from recall_engine.search_engine import SearchEngine


class SearchRequest(BaseModel):
    query: str
    mode: str = "auto"
    top_k: int | None = None


class SearchResponse(BaseModel):
    query: str
    mode: str
    count: int
    results: list[dict[str, Any]]


def create_app(engine: SearchEngine) -> FastAPI:
    app = FastAPI(title="RecallEngine", summary="Keyword, boolean, ranked, semantic and hybrid search")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "documents": engine.indexer.get_total_documents()}

    # Plain def, not async: search is CPU-bound, so FastAPI runs it in its threadpool
    # instead of blocking the event loop.
    @app.post("/search", response_model=SearchResponse)
    def search(search_request: SearchRequest) -> SearchResponse:
        try:
            results = engine.search(search_request.query, mode=search_request.mode, top_k=search_request.top_k)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return SearchResponse(
            query=search_request.query, mode=search_request.mode, count=len(results), results=results
        )

    return app
