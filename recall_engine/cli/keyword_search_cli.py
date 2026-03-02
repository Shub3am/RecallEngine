#!/usr/bin/env python3
import json
import argparse
from nltk.stem import PorterStemmer 
from recall_engine.cli.misc import get_stop_words, dataset_loader
import string


        
def tokens_stemmer(tokens: list[str]) -> list[str]:
    """Reduce tokens to their root forms using Porter Stemming algorithm.
    
    Args:
        tokens: List of word tokens to stem
        
    Returns:
        List of unique stemmed tokens (duplicates removed via dict)
    """
    stemmer = PorterStemmer()
    stemmed_tokens: dict[str, str] = {}
    for token in tokens:
        stemmed_tokens[stemmer.stem(token, to_lowercase=True)] = ""
    return list(stemmed_tokens.keys())

def clean_punctuation(content: str) -> str:
    """Remove all punctuation characters from the given text.
    
    Args:
        content: String containing text to clean
        
    Returns:
        String with all punctuation removed
    """
    punctuations = string.punctuation
    punctuation_table: dict[str, str] = {}
    for punct in punctuations:
        punctuation_table[punct] = ""
    punctuation_table= str.maketrans(punctuation_table)
    return content.translate(punctuation_table)

def remove_stop_words(content_tokens: list[str]) -> list[str]:
    """Filter out common stop words from token list.
    
    Args:
        content_tokens: List of word tokens to filter
        
    Returns:
        List of tokens with stop words removed
    """
    new_token: list[str] = []
    for word_token in content_tokens:
        if (word_token not in get_stop_words()): 
            new_token.append(word_token)
    return new_token
        
def standardize_texts(content: str) -> list[str]:
    """Normalize text through a multi-step pipeline for search matching.
    
    Pipeline: lowercase → remove punctuation → tokenize → remove stop words → stem
    
    Args:
        content: Raw text string to normalize
        
    Returns:
        List of normalized, stemmed tokens
    """
    base = content.lower()
    base = clean_punctuation(base)
    base = base.split(" ")
    base = remove_stop_words(base)
    base = tokens_stemmer(base)
    return base
    
def match_keyword(query: str, content: str) -> bool:
    """Check if query string exists as substring in content (case-insensitive).
    
    Args:
        query: Search term to look for
        content: Text to search within
        
    Returns:
        True if query found in content, False otherwise
    """
    if (query.lower() in content.lower()):
        return True
    return False
        

    
def main() -> None:
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
    movies = json.loads(dataset_loader("./data/movies.json")) # poetry runs from project root, so path is relative to root
    match args.command:
        case "search":
            query = standardize_texts(args.query)
            print(f"Searching for: {args.query}")
            for index,item in enumerate(movies['movies']):
                movie_title = standardize_texts( item['title'])
                for single_query in query:
                    isMatch = False
                    for single_title_token in movie_title:
                        if match_keyword(single_query, single_title_token):
                            isMatch = True
                    if (isMatch):
                        print(f"{index}: {item['title']}")

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
    
    
    
    
    