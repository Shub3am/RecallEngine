#!/usr/bin/env python3
import argparse
from recall_engine.cli.misc import DATA_PATH
from recall_engine.helper.indexer import Indexer

 

    
def cli() -> None:
    """CLI entry point for keyword-based movie search.
    # command to run: poetry run python recall_engine/cli/keyword_search_cli.py search "query string"
    # Provides 'search' subcommand to query movies.json dataset by matching
    # normalized query tokens against normalized movie titles.
    """
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search movies using BM25")
    search_parser.add_argument("query", type=str, help="Search query")

    args = parser.parse_args()
    movies = DATA_PATH # poetry runs from project root, so path is relative to root
    indexer = Indexer()
    indexer.load_or_build(movies, dataKey="movies", docIdKey="id", excludeDocKeys=["id"])
    match args.command:
        case "search":
            # args.query example: "The Godfather"
            print(f"Searching for: {args.query}")
            query = args.query
            operation = args.operation if hasattr(args, 'operation') else None
            if (operation):
                print(f"Using operation: {operation}")
            
            results = indexer.get_documents(query, operation=operation)
            for i, result in enumerate(results):
                print(f"{i+1}. Title: {result['title']}")
        case _:
            parser.print_help()


if __name__ == "__main__":
    cli()
    
    
    
    
    