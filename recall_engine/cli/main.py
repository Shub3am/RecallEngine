#!/usr/bin/env python3
import argparse
import os

from recall_engine.search_engine import SearchEngine
from recall_engine.search_engine.engine import RANKED_MODES, SEARCH_MODES
from recall_engine.search_engine.misc import DATA_PATH

# Read from the environment, not a flag, so the key never shows up in `ps` output.
API_KEY_ENV_VAR = "RECALL_ENGINE_API_KEY"

#example commands:
#  recall_engine search "apple AND banana" --mode boolean --dataset datasets/movies.json --data-key movies
#  recall_engine serve --dataset datasets/movies.json --data-key movies --port 8000


def _search(args: argparse.Namespace, engine: SearchEngine) -> None:
    top_k = args.top_k if args.mode in RANKED_MODES else None

    print(f"Query : {args.query}")
    print(f"Mode  : {args.mode}" + (f"  top_k={top_k}" if top_k else ""))
    print()

    try:
        results = engine.search(args.query, mode=args.mode, top_k=top_k)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    if not results:
        print("No results found.")
        return

    for position, doc in enumerate(results, start=1):
        rank_prefix = f"[{doc['rank']}] score={doc['score']:.4f}  " if "rank" in doc else f"{position}.  "
        title = doc.get("title") or doc.get("text", "")[:80]
        print(f"{rank_prefix}{title}")


def _serve(args: argparse.Namespace, engine: SearchEngine) -> None:
    from recall_engine.api import create_app

    # uvicorn ships with the api extra, which the create_app import above already requires.
    import uvicorn

    uvicorn.run(create_app(engine, api_key=os.environ.get(API_KEY_ENV_VAR)), host=args.host, port=args.port)


def cli() -> None:
    dataset_parser = argparse.ArgumentParser(add_help=False)
    dataset_parser.add_argument(
        "--dataset",
        type=str,
        default=DATA_PATH,
        help="Path to a JSON dataset file (default: datasets/movies.json)",
    )
    dataset_parser.add_argument(
        "--data-key",
        type=str,
        default="movies",
        dest="data_key",
        help="Top-level JSON key that holds the list of documents (default: movies)",
    )

    parser = argparse.ArgumentParser(
        prog="recall_engine",
        description="RecallEngine: keyword, boolean, ranked, semantic and hybrid text search",
    )
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search", parents=[dataset_parser], help="Search a dataset")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument(
        "--mode",
        type=str,
        default="bm25",
        choices=SEARCH_MODES,
        help="Retrieval mode (default: bm25)",
    )
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        dest="top_k",
        help="Number of results to return for ranked modes (default: 10)",
    )
    search_parser.set_defaults(run_command=_search)

    serve_parser = subparsers.add_parser(
        "serve",
        parents=[dataset_parser],
        help=f"Serve a dataset over HTTP (set {API_KEY_ENV_VAR} to require an X-API-Key header)",
    )
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    serve_parser.set_defaults(run_command=_serve)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.run_command(args, SearchEngine.from_json(args.dataset, data_key=args.data_key))


if __name__ == "__main__":
    cli()
