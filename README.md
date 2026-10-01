<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/banner-dark.svg">
  <img alt="RecallEngine: search and RAG over files, folders and databases" src="docs/images/banner-light.svg">
</picture>

<p align="center">
  <a href="https://github.com/Shub3am/RecallEngine/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/Shub3am/RecallEngine/actions/workflows/tests.yml/badge.svg"></a>
  <a href="https://github.com/Shub3am/RecallEngine/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/Shub3am/RecallEngine"></a>
  <a href="https://github.com/Shub3am/RecallEngine/pkgs/container/recallengine"><img alt="Container image" src="https://img.shields.io/badge/ghcr.io-recallengine-2496ED?logo=docker&logoColor=white"></a>
  <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white">
</p>

**Point RecallEngine at a folder of documents or a database and search it, or ask it questions.** One import gives you keyword, boolean, BM25, TF-IDF, semantic and hybrid search over PDFs, Word files, spreadsheets, JSON, Markdown, HTML and SQL tables. Add a Claude API key and it answers questions from your documents, with citations back to the passages it used.

<p align="center">
  <img alt="Searching a folder of mixed documents and a SQLite table from the CLI" src="docs/images/any-source.gif" width="820">
</p>

<p align="center"><a href="docs/demo/recallengine-demo.mp4">Watch the full walkthrough video</a>: the Python library in an editor, a folder of mixed formats from the CLI, boolean search, a SQLite table and the authenticated HTTP API with hybrid search.</p>

## Why RecallEngine

| | |
|---|---|
| **Any source** | A file, a folder, a SQLite file or any SQLAlchemy database URL. Folders are walked, long text is split into overlapping passages. |
| **Every search mode** | Exact keyword, boolean (`AND`, `OR`, `NOT`, parentheses), BM25, TF-IDF, semantic embeddings and hybrid rank fusion. |
| **RAG building blocks** | Ingest many sources into one saved index, embed it once, and `retrieve` passages for any model. |
| **Cited answers** | `ask` retrieves the best passages and has Claude answer from them only, with numbered citations. |
| **Library, CLI or HTTP** | The same engine from Python, the `recall_engine` command or a FastAPI server with optional API key auth. |
| **Light by default** | The core has no heavy dependencies. PDF parsing, embeddings, databases, the server and Claude are opt-in extras. |
| **Cached** | Indexes and embeddings are cached on disk and rebuilt only when the source changes. |

## Install

```bash
# Everything
pip install "recall-engine[all] @ git+https://github.com/Shub3am/RecallEngine"

# Core only: keyword, boolean, BM25, TF-IDF over JSON, JSONL, CSV, TXT, MD and HTML
pip install "recall-engine @ git+https://github.com/Shub3am/RecallEngine"
```

Wheels are also attached to every [GitHub release](https://github.com/Shub3am/RecallEngine/releases). Requires Python 3.12 or newer.

| Extra      | Adds                                                    |
|------------|---------------------------------------------------------|
| `formats`  | PDF, DOCX and XLSX files                                |
| `database` | Database URLs through SQLAlchemy (SQLite files work without it) |
| `semantic` | `semantic` and `hybrid` search modes (fastembed)        |
| `rag`      | `ask`: cited answers from Claude                        |
| `api`      | `recall_engine serve` and `create_app`                  |
| `all`      | All of the above                                        |

## Supported sources

| Source | How it becomes documents |
|---|---|
| `.json` | One document per item in the list (pick the list with `data_key` if there are several) |
| `.jsonl` | One document per line |
| `.csv`, `.tsv` | One document per row, columns kept as fields |
| `.xlsx` | One document per row, across every sheet (`formats`) |
| `.txt`, `.md`, `.html` | Text split into overlapping passages |
| `.pdf`, `.docx` | Text extracted, then split into passages (`formats`) |
| Folder | Every supported file inside it, hidden files skipped |
| `.db`, `.sqlite`, `.sqlite3` | One document per row of every table, one `table`, or a `query`. Opened read-only, no extra needed |
| Database URL (`postgresql://...`, `sqlite:///...`) | Same, through SQLAlchemy (`database` extra plus the database's driver) |

Every document gets a stable `passage_id` such as `handbook.md#3` or `products#12`, and a `source` field saying where it came from.

## Quick start

```python
from recall_engine import SearchEngine

engine = SearchEngine.from_source("./docs")

engine.search("refund policy", mode="bm25", top_k=5)
engine.search("refund AND NOT enterprise")                 # boolean, picked automatically
engine.search("how do I get my money back", mode="hybrid", top_k=5)

answer = engine.ask("How long do customers have to ask for a refund?")
print(answer["answer"])
for citation in answer["citations"]:
    print(citation["number"], citation["passage_id"], citation["cited_text"])
```

`ask` needs the `rag` extra and `ANTHROPIC_API_KEY` in the environment. It returns `{"question", "answer", "citations"}`, and each citation points at the `passage_id` it came from.

Databases work the same way:

```python
SearchEngine.from_source("shop.db", table="products")
SearchEngine.from_source("postgresql://user:pass@host/db", query="select id, title, body from articles")
```

Already have the documents in memory, or a JSON file with your own ids:

```python
SearchEngine.from_documents([{"id": "1", "title": "Red Apple", "overview": "fresh fruit"}])
SearchEngine.from_json("movies.json", data_key="movies")
```

## RAG pipeline: ingest, embed, retrieve

Build a knowledge base from several sources once, then retrieve passages for any model's prompt, or let `ask` hand them to Claude:

```python
engine = SearchEngine.from_source(["./handbook", "./policies", "shop.db"], cache_path="kb.pkl")
engine.embed()                                  # embed every passage now, cached next to the index

engine = SearchEngine.from_index("kb.pkl")      # later: reopen without reading the sources
for passage in engine.retrieve("how do I get my money back", mode="hybrid", top_k=5):
    print(passage["rank"], passage["id"], passage["text"])
```

```bash
recall_engine ingest ./handbook ./policies --index kb.pkl --embed
recall_engine retrieve "how do I get my money back" --index kb.pkl --mode hybrid
curl -X POST localhost:8000/retrieve -H 'content-type: application/json' -d '{"query": "refund window"}'
```

Each passage comes back as `{"rank", "score", "id", "text", "document"}`. Choose the embedding model with `embedding_model=` or `--embedding-model`, and use the same one when reopening the index.

## CLI

<p align="center">
  <img alt="BM25, boolean and hybrid search over a movie dataset" src="docs/images/search-modes.gif" width="820">
</p>

```bash
recall_engine search "refund policy" --dataset ./docs --mode bm25 --top-k 5
recall_engine search "desk" --dataset shop.db --table products
recall_engine ask "How long do customers have to ask for a refund?" --dataset ./docs
recall_engine serve --dataset ./docs --port 8000
recall_engine ingest ./docs ./policies --index kb.pkl --embed
recall_engine retrieve "refund window" --index kb.pkl --top-k 3
```

`ask` prints the answer, then a `Sources:` list with each citation's passage id and the quoted text.

## HTTP API

<p align="center">
  <img alt="Health check, keyword search and authenticated hybrid search over HTTP" src="docs/images/http-api.gif" width="820">
</p>

| Endpoint | Body | Returns |
|---|---|---|
| `GET /health` | | `{"status", "documents"}` |
| `POST /search` | `{"query", "mode", "top_k"}` | `{"query", "mode", "count", "results"}` |
| `POST /retrieve` | `{"query", "mode", "top_k"}` | `{"query", "mode", "count", "passages"}` |
| `POST /ask` | `{"question", "mode", "top_k"}` | `{"question", "answer", "citations"}` |

```bash
curl -X POST localhost:8000/search -H 'content-type: application/json' \
  -d '{"query": "encrypted backups", "mode": "bm25", "top_k": 3}'

curl -X POST localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question": "Are backups encrypted?"}'
```

Invalid modes, malformed boolean queries and questions with no matching documents return 400. Interactive docs are served at `/docs`.

<p align="center">
  <img alt="Swagger UI listing the health, search and ask endpoints" src="docs/images/api-docs.png" width="820">
</p>

Set `RECALL_ENGINE_API_KEY` before `recall_engine serve` to require an `X-API-Key` header on `/search`, `/retrieve` and `/ask`. `/health` stays open for load balancer probes. The server binds to `127.0.0.1` by default; pass `--host 0.0.0.0` to expose it, and put TLS in front of it.

Mount it in your own app:

```python
from recall_engine.api import create_app

app = create_app(SearchEngine.from_source("./docs"), api_key="your-secret")
```

## Docker

```bash
docker run --rm -p 8000:8000 -v ./docs:/data \
  -e ANTHROPIC_API_KEY -e RECALL_ENGINE_API_KEY=your-secret \
  ghcr.io/shub3am/recallengine
```

The image has every extra installed and serves whatever you mount at `/data`: a folder, a single file or a SQLite database. Images are published for `linux/amd64` and `linux/arm64`.

## Search modes

| Mode       | What it does                                                         | `top_k` |
|------------|----------------------------------------------------------------------|---------|
| `auto`     | `boolean` if the query has AND, OR, NOT or parentheses, otherwise `keyword` | No |
| `keyword`  | Documents containing any query term, sorted by id                    | No      |
| `boolean`  | AND, OR, NOT and parentheses, sorted by id                           | No      |
| `bm25`     | Ranked by BM25                                                       | Yes     |
| `tfidf`    | Ranked by TF-IDF                                                     | Yes     |
| `semantic` | Ranked by embedding similarity (`BAAI/bge-small-en-v1.5`)            | Yes     |
| `hybrid`   | BM25 and semantic rankings merged with Reciprocal Rank Fusion        | Yes     |

Ranked results carry two extra fields: `score` and `rank`. `retrieve` and `ask` accept the ranked modes and default to `bm25` with the top 5 passages.

The first semantic search downloads the embedding model (about 70 MB) and embeds every document. For files and folders the embeddings are cached next to the index. Database URLs are reloaded on every start, because there is no cheap way to tell whether a remote database changed.

## More

- [USAGE.md](USAGE.md): the full guide.
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md): working on the code.
- [docs/demo/](docs/demo/): the sample documents and the [vhs](https://github.com/charmbracelet/vhs) tapes that record the GIFs above.

## Status

Version 1.2.0.
