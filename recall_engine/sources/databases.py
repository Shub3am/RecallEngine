"""Reads database tables or a query result into plain records, grouped by source label.

Exists so SQLite files work with the standard library alone and every other
database works through SQLAlchemy. Must not assign passage ids, parse document
files, or know anything about indexing or search.
"""
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from recall_engine.sources.files import json_safe_value

MISSING_DATABASE_EXTRA = 'Database URLs need the optional extra: pip install "recall-engine[database]"'
SQLITE_SUFFIXES = (".db", ".sqlite", ".sqlite3")
QUERY_SOURCE_LABEL = "query"


def row_record(column_names: list[str], row_values: tuple[Any, ...]) -> dict[str, Any]:
    return {name: json_safe_value(value) for name, value in zip(column_names, row_values)}


def read_sqlite_record_groups(
    path: Path, table: str | None, query: str | None
) -> list[tuple[str, list[dict[str, Any]]]]:
    # mode=ro so a load can never create or modify the database file.
    with closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)) as connection:
        if query is not None:
            return [(QUERY_SOURCE_LABEL, sqlite_query_records(connection, query))]
        if table is not None:
            table_names = [table]
        else:
            table_names = [
                name
                for (name,) in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
        return [(name, sqlite_query_records(connection, f"SELECT * FROM {quote_sqlite_identifier(name)}")) for name in table_names]


def quote_sqlite_identifier(name: str) -> str:
    escaped_name = name.replace('"', '""')
    return f'"{escaped_name}"'


def sqlite_query_records(connection: sqlite3.Connection, query: str) -> list[dict[str, Any]]:
    cursor = connection.execute(query)
    column_names = [column[0] for column in cursor.description]
    return [row_record(column_names, row) for row in cursor.fetchall()]


def read_database_url_record_groups(
    url: str, table: str | None, query: str | None
) -> list[tuple[str, list[dict[str, Any]]]]:
    try:
        import sqlalchemy
    except ImportError as error:
        raise ImportError(MISSING_DATABASE_EXTRA) from error

    engine = sqlalchemy.create_engine(url)
    try:
        with engine.connect() as connection:
            if query is not None:
                result = connection.execute(sqlalchemy.text(query))
                return [(QUERY_SOURCE_LABEL, [row_record(list(result.keys()), tuple(row)) for row in result])]
            table_names = [table] if table is not None else sqlalchemy.inspect(engine).get_table_names()
            metadata = sqlalchemy.MetaData()
            record_groups = []
            for name in table_names:
                reflected_table = sqlalchemy.Table(name, metadata, autoload_with=connection)
                result = connection.execute(sqlalchemy.select(reflected_table))
                record_groups.append((name, [row_record(list(result.keys()), tuple(row)) for row in result]))
            return record_groups
    finally:
        engine.dispose()
