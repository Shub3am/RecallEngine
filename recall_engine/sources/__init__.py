"""Turns a file, a folder or a database into a flat list of documents with stable passage ids.

Exists so callers can index any source through one call and know when a cached
index is still valid. Must not import search_engine, api, cli or rag, and must
not know anything about indexing or search.
"""
from pathlib import Path
from typing import Any

from recall_engine.sources.chunking import CHUNK_OVERLAP_WORDS, CHUNK_WORDS
from recall_engine.sources.databases import (
    SQLITE_SUFFIXES,
    read_database_url_record_groups,
    read_sqlite_record_groups,
)
from recall_engine.sources.files import SUPPORTED_FILE_SUFFIXES, list_source_files, read_file_records

PASSAGE_ID_KEY = "passage_id"
SOURCE_KEY = "source"

__all__ = ["load_documents", "source_fingerprint", "PASSAGE_ID_KEY", "SOURCE_KEY", "SUPPORTED_FILE_SUFFIXES"]


def detect_source_kind(source: str) -> str:
    if "://" in source:
        return "url"
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    if path.is_dir():
        return "folder"
    suffix = path.suffix.lower()
    if suffix in SQLITE_SUFFIXES:
        return "sqlite"
    if suffix in SUPPORTED_FILE_SUFFIXES:
        return "file"
    supported_suffixes = ", ".join(SUPPORTED_FILE_SUFFIXES + SQLITE_SUFFIXES)
    raise ValueError(f"Unsupported file type {suffix!r} for {source}. Supported: {supported_suffixes}")


def load_documents(
    source: str, data_key: str = "", table: str | None = None, query: str | None = None
) -> list[dict[str, Any]]:
    source_kind = detect_source_kind(source)
    if source_kind == "url":
        record_groups = read_database_url_record_groups(source, table, query)
    elif source_kind == "sqlite":
        record_groups = read_sqlite_record_groups(Path(source), table, query)
    elif source_kind == "folder":
        folder = Path(source)
        record_groups = [
            (file_path.relative_to(folder).as_posix(), read_file_records(file_path, data_key))
            for file_path in list_source_files(folder)
        ]
    else:
        file_path = Path(source)
        record_groups = [(file_path.name, read_file_records(file_path, data_key))]

    documents = []
    for source_label, records in record_groups:
        for position, record in enumerate(records, start=1):
            documents.append({**record, PASSAGE_ID_KEY: f"{source_label}#{position}", SOURCE_KEY: source_label})
    return documents


def source_fingerprint(
    source: str, data_key: str = "", table: str | None = None, query: str | None = None
) -> dict[str, Any] | None:
    source_kind = detect_source_kind(source)
    if source_kind == "url":
        return None
    path = Path(source).resolve()
    chunk_settings = {"chunk_words": CHUNK_WORDS, "chunk_overlap_words": CHUNK_OVERLAP_WORDS}
    if source_kind == "folder":
        folder_files = []
        for file_path in list_source_files(path):
            file_stat = file_path.stat()
            folder_files.append([file_path.relative_to(path).as_posix(), file_stat.st_size, file_stat.st_mtime_ns])
        return {"kind": "folder", "path": str(path), "files": folder_files, "data_key": data_key, **chunk_settings}
    path_stat = path.stat()
    if source_kind == "sqlite":
        return {
            "kind": "sqlite",
            "path": str(path),
            "size": path_stat.st_size,
            "mtime_ns": path_stat.st_mtime_ns,
            "table": table,
            "query": query,
        }
    return {
        "kind": "file",
        "path": str(path),
        "size": path_stat.st_size,
        "mtime_ns": path_stat.st_mtime_ns,
        "data_key": data_key,
        **chunk_settings,
    }
