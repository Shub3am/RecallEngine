# sources

## Owns

Turning a source string (a file, a folder, a SQLite file or a SQLAlchemy database URL) into a flat list of document dicts with stable passage ids, and a stat-only fingerprint that tells the caller whether a cached index built from that source is still valid. Also owns splitting long text into overlapping passages.

## Must not know about

Indexing, ranking, search modes, cache file locations, HTTP or argparse. Nothing here imports `search_engine`, `api`, `cli` or `rag`.

## Entry points

- `load_documents(source, data_key, table, query)`: raises `FileNotFoundError` for a missing path and `ValueError` for an unsupported suffix or a `data_key` that is not in the JSON.
- `source_fingerprint(...)`: same arguments and the same detection rules; returns `None` for database URLs.
- `PASSAGE_ID_KEY`, `SOURCE_KEY`, `SUPPORTED_FILE_SUFFIXES` from `__init__.py`.

## Invariants and gotchas

- Detection order: `"://"` in the string means a database URL; then an existing directory is walked; then `.db`, `.sqlite`, `.sqlite3` is a SQLite file; anything else is one file. Folder walks never load SQLite files, only `SUPPORTED_FILE_SUFFIXES`.
- Folder walks skip hidden files and hidden directories (names starting with `.`) and silently skip unsupported suffixes. Order is by relative posix path, so ids are deterministic across runs and machines.
- `passage_id` is `<label>#<n>` with `n` counting from 1 per label. The label is the posix path relative to the folder root (just the file name for a single file), the table name for databases, or `query` for a custom query. XLSX numbering continues across sheets in one file. Adding a file to a folder never shifts ids of other files; adding rows mid-file does shift later ids in that file.
- `passage_id` and `source` always overwrite fields of the same name in the original record.
- Structured records (JSON, JSONL, CSV/TSV, XLSX, database rows) keep every original field. Only XLSX and database values that are not str, int, float, bool or None are passed through `str()`; JSON values are left untouched. CSV values are always strings.
- `table` and `query` only affect databases; `query` wins when both are given. `data_key` only affects `.json` files, including those inside a folder.
- SQLite files open read-only (`mode=ro`), so a load can never create or change the database.
- pypdf, python-docx and openpyxl (`formats` extra) and SQLAlchemy (`database` extra) are imported lazily inside the reader that needs them. Importing them at module level breaks installs without the extra.
- The fingerprint reads `stat()` only, never file contents. It includes `data_key` and the chunk settings (`CHUNK_WORDS` 200, `CHUNK_OVERLAP_WORDS` 40), so changing chunking invalidates caches. A SQLite database in WAL mode can change without the main file's mtime moving until a checkpoint.
- Database URLs have no fingerprint (`None`) because there is no cheap way to tell whether a remote database changed; callers must rebuild every time and must not cache.

## Called by

`recall_engine/search_engine/engine.py` via `SearchEngine.from_source`, and `tests/test_sources.py`.
