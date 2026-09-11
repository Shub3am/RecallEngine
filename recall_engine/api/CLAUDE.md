# api

## Owns

The FastAPI app: request and response models, the `/health` and `/search` routes, optional `X-API-Key` auth, and mapping engine errors to HTTP status codes.

## Must not know about

Datasets, files, cache paths or CLI arguments. `create_app(engine, api_key)` receives a ready `SearchEngine`, so it works for any dataset and any host app.

## Entry points

- `create_app(engine, api_key=None)`.

## Invariants and gotchas

- fastapi and pydantic are only available with the `api` extra; importing this package without them raises an `ImportError` naming the extra.
- `/search` is a plain `def`, not `async def`, so FastAPI runs the CPU-bound search in its threadpool. The engine must stay thread-safe for that reason.
- `ValueError` from the engine becomes 400; missing or invalid request fields are 422 from pydantic; a missing or wrong key is 401.
- `/health` is never behind the API key so load balancers can probe it.
- Keys are compared with `secrets.compare_digest`.

## Called by

`recall_engine/cli/main.py` (`serve`), users mounting it in their own ASGI server, and `tests/test_api.py`.
