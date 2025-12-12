#!/usr/bin/env python3
import json
import argparse
from recall_engine.cli.misc import  dataset_loader
from recall_engine.cli.misc import DATA_PATH
from recall_engine.helper.tokenizer import Tokenizer

 

    
def cli() -> None:
    """CLI entry point for keyword-based movie search.
    //command t o run: poetry run python recall_engine/cli/keyword_search_cli.py search "query string"
    Provides 'search' subcommand to query movies.json dataset by matching
    normalized query tokens against normalized movie titles.
    """
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search movies using BM25")
    search_parser.add_argument("query", type=str, help="Search query")

    args = parser.parse_args()
    movies = json.loads(dataset_loader(DATA_PATH)) # poetry runs from project root, so path is relative to root
    match args.command:
        case "search":
            tokenizer = Tokenizer()
            # args.query example: "The Godfather"
            query = tokenizer.tokenize(args.query)
            print(f"Searching for: {args.query}")
            for index,item in enumerate(movies['movies']):
                movie_title = tokenizer.tokenize(item['title'])
                for single_query in query:
                    isMatch = False
                    for single_title_token in movie_title:
                        if tokenizer.match_keyword(single_query, single_title_token):
                            isMatch = True
                    if (isMatch):
                        print(f"{index}: {item['title']}")

        case _:
            parser.print_help()


if __name__ == "__main__":
    cli()
    
    
    
    
    