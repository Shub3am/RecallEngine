#!/usr/bin/env python3
import argparse
import os

from recall_engine.search_engine import SearchEngine
from recall_engine.search_engine.engine import (
    RETRIEVAL_MODES,
    DEFAULT_RETRIEVAL_MODE,
    DEFAULT_RETRIEVAL_TOP_K,
    RANKED_MODES,
    SEARCH_MODES,
)
from recall_engine.search_engine.misc import DATA_PATH

# Read from the environment, not a flag, so the key never shows up in `ps` output.
API_KEY_ENV_VAR = "RECALL_ENGINE_API_KEY"
RESULT_SNIPPET_CHARS = 80

#example commands:
#  recall_engine search "apple AND banana" --mode boolean --dataset datasets/movies.json
#  recall_engine search "refund policy" --dataset ./docs
#  recall_engine ask "what is the refund window?" --dataset ./docs
#  recall_engine serve --dataset sqlite:///shop.db --table products --port 8000
#  recall_engine ingest ./docs ./policies --index ./kb.pkl --embed
#  recall_engine retrieve "refund window" --index ./kb.pkl --mode hybrid


def _open_engine(args: argparse.Namespace) -> SearchEngine:
    if args.index:
        return SearchEngine.from_index(args.index, embedding_model=args.embedding_model)
    return SearchEngine.from_source(
        args.dataset, data_key=args.data_key, table=args.table, query=args.sql, embedding_model=args.embedding_model
    )


def _ingest(args: argparse.Namespace) -> None:
    engine = SearchEngine.from_source(
        args.sources,
        data_key=args.data_key,
        table=args.table,
        query=args.sql,
        cache_path=args.index,
        embedding_model=args.embedding_model,
    )
    # from_source only writes caches for file-backed sources; saving here also keeps a snapshot of database URLs.
    engine.indexer.save()
    print(f"Indexed {len(engine.indexer.get_doc_map())} passages into {args.index}")
    if not args.embed:
        return
    embedded_count = engine.embed()
    if engine.indexer.source_fingerprint is None:
        print(f"Embedded {embedded_count} passages (not cached: a database URL source has no fingerprint to key them on)")
    else:
        print(f"Embedded {embedded_count} passages")


def _search(args: argparse.Namespace) -> None:
    engine = _open_engine(args)
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
        print(f"{rank_prefix}{_result_label(doc, engine)}")


def _result_label(doc: dict, engine: SearchEngine) -> str:
    doc_id = str(doc[engine.indexer.doc_id_key])
    snippet = doc.get("title") or " ".join(engine.indexer.get_document_text(doc_id).split())[:RESULT_SNIPPET_CHARS]
    return f"{doc_id}  {snippet}"


def _retrieve(args: argparse.Namespace) -> None:
    engine = _open_engine(args)
    try:
        passages = engine.retrieve(args.query, mode=args.mode, top_k=args.top_k)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    if not passages:
        print("No passages matched.")
        return
    for passage in passages:
        print(f"[{passage['rank']}] score={passage['score']:.4f}  {passage['id']}")
        print(f"    {' '.join(passage['text'].split())}")


def _ask(args: argparse.Namespace) -> None:
    engine = _open_engine(args)
    try:
        answer = engine.ask(args.question, mode=args.mode, top_k=args.top_k)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    print(answer["answer"])
    if answer["citations"]:
        print()
        print("Sources:")
    for citation in answer["citations"]:
        print(f"  [{citation['number']}] {citation['passage_id']}: \"{citation['cited_text'].strip()}\"")


def _serve(args: argparse.Namespace) -> None:
    from recall_engine.api import create_app

    # uvicorn ships with the api extra, which the create_app import above already requires.
    import uvicorn

    engine = _open_engine(args)
    uvicorn.run(create_app(engine, api_key=os.environ.get(API_KEY_ENV_VAR)), host=args.host, port=args.port)


def cli() -> None:
    source_options_parser = argparse.ArgumentParser(add_help=False)
    source_options_parser.add_argument(
        "--data-key",
        type=str,
        default="",
        dest="data_key",
        help="Top-level JSON key that holds the list of documents (default: the only list in the file)",
    )
    source_options_parser.add_argument(
        "--table", type=str, default=None, help="Database table to index (default: all)"
    )
    # Named --sql, not --query, because `search` already uses `query` for the search text.
    source_options_parser.add_argument(
        "--sql", type=str, default=None, help="SQL query whose rows are indexed instead of whole tables"
    )
    source_options_parser.add_argument(
        "--embedding-model",
        type=str,
        default=None,
        dest="embedding_model",
        help="fastembed model for semantic and hybrid modes (default: BAAI/bge-small-en-v1.5)",
    )

    dataset_parser = argparse.ArgumentParser(add_help=False, parents=[source_options_parser])
    dataset_choice = dataset_parser.add_mutually_exclusive_group()
    dataset_choice.add_argument(
        "--dataset",
        type=str,
        default=DATA_PATH,
        help="File, folder or database URL to index (default: datasets/movies.json)",
    )
    dataset_choice.add_argument(
        "--index", type=str, default=None, help="Index saved by `ingest` to open instead of reading a dataset"
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

    ingest_parser = subparsers.add_parser(
        "ingest", parents=[source_options_parser], help="Index files, folders and databases into one saved index"
    )
    ingest_parser.add_argument("sources", nargs="+", help="Files, folders or database URLs to ingest")
    ingest_parser.add_argument("--index", type=str, required=True, help="Where to save the index")
    ingest_parser.add_argument(
        "--embed", action="store_true", help="Embed every passage now so semantic and hybrid queries start fast"
    )
    ingest_parser.set_defaults(run_command=_ingest)

    retrieve_parser = subparsers.add_parser(
        "retrieve", parents=[dataset_parser], help="Print the top passages for a query, for use in any model's prompt"
    )
    retrieve_parser.add_argument("query", type=str, help="Search query")
    retrieve_parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_RETRIEVAL_MODE,
        choices=RETRIEVAL_MODES,
        help=f"Retrieval mode (default: {DEFAULT_RETRIEVAL_MODE})",
    )
    retrieve_parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_RETRIEVAL_TOP_K,
        dest="top_k",
        help=f"Number of passages to return (default: {DEFAULT_RETRIEVAL_TOP_K})",
    )
    retrieve_parser.set_defaults(run_command=_retrieve)

    ask_parser = subparsers.add_parser(
        "ask", parents=[dataset_parser], help="Answer a question from the dataset with Claude (needs ANTHROPIC_API_KEY)"
    )
    ask_parser.add_argument("question", type=str, help="Question to answer")
    ask_parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_RETRIEVAL_MODE,
        choices=RETRIEVAL_MODES,
        help=f"Retrieval mode used to pick passages (default: {DEFAULT_RETRIEVAL_MODE})",
    )
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_RETRIEVAL_TOP_K,
        dest="top_k",
        help=f"Number of passages sent to Claude (default: {DEFAULT_RETRIEVAL_TOP_K})",
    )
    ask_parser.set_defaults(run_command=_ask)

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

    args.run_command(args)


if __name__ == "__main__":
    cli()
