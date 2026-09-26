"""Reads document files into plain records, one reader per format.

Exists so each file format has one place that knows how to parse it and which
folder entries count as loadable files. Must not assign passage ids, know about
databases, or know anything about indexing or search.
"""
import csv
import importlib
import json
import os
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType
from typing import Any

from recall_engine.sources.chunking import chunk_text

MISSING_FORMATS_EXTRA = 'PDF, DOCX and XLSX files need the optional extra: pip install "recall-engine[formats]"'

JSON_SUFFIXES = (".json",)
JSON_LINES_SUFFIXES = (".jsonl", ".ndjson")
DELIMITED_SUFFIXES = (".csv", ".tsv")
PLAIN_TEXT_SUFFIXES = (".txt", ".md", ".markdown")
HTML_SUFFIXES = (".html", ".htm")
SUPPORTED_FILE_SUFFIXES = tuple(
    sorted(
        JSON_SUFFIXES
        + JSON_LINES_SUFFIXES
        + DELIMITED_SUFFIXES
        + PLAIN_TEXT_SUFFIXES
        + HTML_SUFFIXES
        + (".pdf", ".docx", ".xlsx")
    )
)


def list_source_files(folder: Path) -> list[Path]:
    """Every supported, non-hidden file under folder, ordered by relative posix path."""
    source_files = []
    for directory, subdirectory_names, file_names in os.walk(folder):
        subdirectory_names[:] = [name for name in subdirectory_names if not name.startswith(".")]
        for file_name in file_names:
            file_path = Path(directory) / file_name
            if not file_name.startswith(".") and file_path.suffix.lower() in SUPPORTED_FILE_SUFFIXES:
                source_files.append(file_path)
    return sorted(source_files, key=lambda file_path: file_path.relative_to(folder).as_posix())


def read_file_records(path: Path, data_key: str = "") -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in JSON_SUFFIXES:
        return read_json_records(path, data_key)
    if suffix in JSON_LINES_SUFFIXES:
        return read_json_lines_records(path)
    if suffix in DELIMITED_SUFFIXES:
        return read_delimited_records(path)
    if suffix in PLAIN_TEXT_SUFFIXES:
        return text_records(path.read_text(encoding="utf-8"))
    if suffix in HTML_SUFFIXES:
        return text_records(extract_visible_html_text(path.read_text(encoding="utf-8")))
    if suffix == ".pdf":
        return read_pdf_records(path)
    if suffix == ".docx":
        return read_docx_records(path)
    if suffix == ".xlsx":
        return read_xlsx_records(path)
    raise ValueError(f"Unsupported file type {suffix!r}. Supported: {', '.join(SUPPORTED_FILE_SUFFIXES)}")


def json_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def text_records(text: str) -> list[dict[str, Any]]:
    return [{"text": chunk} for chunk in chunk_text(text)]


def read_json_records(path: Path, data_key: str) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as json_file:
        parsed_json = json.load(json_file)
    if isinstance(parsed_json, list):
        return [item for item in parsed_json if isinstance(item, dict)]
    if data_key:
        if data_key not in parsed_json:
            raise ValueError(f"Key {data_key!r} not found in {path.name}")
        return [item for item in parsed_json[data_key] if isinstance(item, dict)]
    list_values = [value for value in parsed_json.values() if isinstance(value, list)]
    if len(list_values) == 1:
        return [item for item in list_values[0] if isinstance(item, dict)]
    return [parsed_json]


def read_json_lines_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as json_lines_file:
        parsed_lines = [json.loads(line) for line in json_lines_file if line.strip()]
    return [record for record in parsed_lines if isinstance(record, dict)]


def read_delimited_records(path: Path) -> list[dict[str, Any]]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open(encoding="utf-8", newline="") as delimited_file:
        return list(csv.DictReader(delimited_file, delimiter=delimiter))


class VisibleTextParser(HTMLParser):
    """Collects the text a browser would show, ignoring script, style and head contents."""

    HIDDEN_TAGS = {"script", "style", "head"}

    def __init__(self) -> None:
        super().__init__()
        self.hidden_depth = 0
        self.visible_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.HIDDEN_TAGS:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.HIDDEN_TAGS and self.hidden_depth > 0:
            self.hidden_depth -= 1

    def handle_data(self, text: str) -> None:
        if self.hidden_depth == 0:
            self.visible_parts.append(text)


def extract_visible_html_text(html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html)
    parser.close()
    return " ".join(" ".join(parser.visible_parts).split())


def import_formats_module(module_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ImportError as error:
        raise ImportError(MISSING_FORMATS_EXTRA) from error


def read_pdf_records(path: Path) -> list[dict[str, Any]]:
    pypdf = import_formats_module("pypdf")
    reader = pypdf.PdfReader(path)
    records = []
    for page_number, page in enumerate(reader.pages, start=1):
        for chunk in chunk_text(page.extract_text()):
            records.append({"text": chunk, "page": page_number})
    return records


def read_docx_records(path: Path) -> list[dict[str, Any]]:
    docx = import_formats_module("docx")
    document = docx.Document(str(path))
    return text_records("\n".join(paragraph.text for paragraph in document.paragraphs))


def read_xlsx_records(path: Path) -> list[dict[str, Any]]:
    openpyxl = import_formats_module("openpyxl")
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    records = []
    try:
        for worksheet in workbook.worksheets:
            rows = worksheet.iter_rows(values_only=True)
            header_row = next(rows, None)
            if header_row is None:
                continue
            headers = ["" if header is None else str(header) for header in header_row]
            for row in rows:
                if all(value is None for value in row):
                    continue
                record = {header: json_safe_value(value) for header, value in zip(headers, row) if header}
                record["sheet"] = worksheet.title
                records.append(record)
    finally:
        # Read-only workbooks keep the file handle open until closed explicitly.
        workbook.close()
    return records
