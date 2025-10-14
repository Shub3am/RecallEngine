#!/usr/bin/env python3
import json
import argparse
from nltk.stem import PorterStemmer
from misc import get_stop_words, dataset_loader
import string

        
def tokens_stemmer(tokens):
    stemmer = PorterStemmer()
    stemmed_tokens = {}
    for token in tokens:
        stemmed_tokens[stemmer.stem(token, to_lowercase=True)] = ""
    return list(stemmed_tokens.keys())

def clean_punctuation(content):
    punctuations = string.punctuation
    punctuation_table = {}
    for punct in punctuations:
        punctuation_table[punct] = ""
    punctuation_table = str.maketrans(punctuation_table)
    return content.translate(punctuation_table)

def remove_stop_words(content_tokens):
    new_token = []
    for word_token in content_tokens:
        if (word_token not in get_stop_words()):
            new_token.append(word_token)
    return new_token
        
def standardize_texts(content: str):
    base = content.lower()
    base = clean_punctuation(base)
    base = content.split(" ")
    base = remove_stop_words(base)
    base = tokens_stemmer(base)
    
    
    
    return base
    
def match_keyword(query, content):
    if (query.lower() in content.lower()):
        return True
    return False
        

    
def main() -> None:
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search movies using BM25")
    search_parser.add_argument("query", type=str, help="Search query")

    args = parser.parse_args()
    movies = json.loads(dataset_loader("./data/movies.json"))
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
    
    
    
    
    