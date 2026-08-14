"""Serves an already built SearchEngine over HTTP.

Must not build or load indexes, read files, or parse CLI arguments; the caller
hands it a ready engine so the same app works for any dataset.
"""
import secrets
from typing import Any

MISSING_API_EXTRA = 'The HTTP API needs the optional extra: pip install "recall-engine[api]"'

try:
    from fastapi import Depends, FastAPI, HTTPException
    from fastapi.security import APIKeyHeader
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


def create_app(engine: SearchEngine, api_key: str | None = None) -> FastAPI:
    app = FastAPI(title="RecallEngine", summary="Keyword, boolean, ranked, semantic and hybrid search")
    api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

    def require_api_key(provided_api_key: str | None = Depends(api_key_header)) -> None:
        if api_key is None:
            return
        # compare_digest keeps the comparison time independent of how many characters match.
        if provided_api_key is None or not secrets.compare_digest(provided_api_key, api_key):
            raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "documents": engine.indexer.get_total_documents()}

    # Plain def, not async: search is CPU-bound, so FastAPI runs it in its threadpool
    # instead of blocking the event loop.
    @app.post("/search", response_model=SearchResponse, dependencies=[Depends(require_api_key)])
    def search(search_request: SearchRequest) -> SearchResponse:
        try:
            results = engine.search(search_request.query, mode=search_request.mode, top_k=search_request.top_k)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return SearchResponse(
            query=search_request.query, mode=search_request.mode, count=len(results), results=results
        )

    return app
