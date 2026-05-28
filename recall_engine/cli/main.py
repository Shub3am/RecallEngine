#!/usr/bin/env python3
import argparse

from recall_engine.search_engine import SearchEngine
from recall_engine.search_engine.misc import DATA_PATH

_RANKED_MODES = {"bm25", "tfidf"}

#example command: recall_engine search "apple AND banana" --mode boolean --dataset datasets/movies.json --data-key movies

def cli() -> None:
    parser = argparse.ArgumentParser(
        prog="recall_engine",
        description="RecallEngine — keyword, boolean, and ranked text search",
    )
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search", help="Search a dataset")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument(
        "--mode",
        type=str,
        default="bm25",
        choices=["keyword", "boolean", "bm25", "tfidf", "auto"],
        help="Retrieval mode (default: bm25)",
    )
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        dest="top_k",
        help="Number of results to return for ranked modes (default: 10)",
    )
    search_parser.add_argument(
        "--dataset",
        type=str,
        default=DATA_PATH,
        help="Path to a JSON dataset file (default: datasets/movies.json)",
    )
    search_parser.add_argument(
        "--data-key",
        type=str,
        default="movies",
        dest="data_key",
        help="Top-level JSON key that holds the list of documents (default: movies)",
    )

    args = parser.parse_args()

    if args.command != "search":
        parser.print_help()
        return

    engine = SearchEngine()
    engine.load_or_build_index(
        doc_path=args.dataset,
        data_key=args.data_key,
        doc_id_key="id",
        exclude_doc_keys=["id"],
    )

    top_k = args.top_k if args.mode in _RANKED_MODES else None

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

    for doc in results:
        rank_prefix = f"[{doc['rank']}] score={doc['score']:.4f}  " if "rank" in doc else f"{results.index(doc) + 1}.  "
        title = doc.get("title") or doc.get("text", "")[:80]
        print(f"{rank_prefix}{title}")


if __name__ == "__main__":
    cli()
