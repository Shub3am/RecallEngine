from pathlib import Path

import pytest

from recall_engine.cli.main import cli
from recall_engine.sources.files import MISSING_FORMATS_EXTRA
from tests.test_rag_pipeline import two_folders  # noqa: F401  (pytest fixture, shared with the pipeline tests)
from tests.test_sources import sqlite_path  # noqa: F401  (pytest fixture)

#Test Command: uv run pytest tests/test_cli.py -v


def run_cli(monkeypatch, capsys, *arguments: str) -> str:
    monkeypatch.setattr("sys.argv", ["recall_engine", *arguments])
    cli()
    return capsys.readouterr().out


def test_ingest_saves_one_index_from_several_sources(monkeypatch, capsys, two_folders: list[str], tmp_path: Path):
    index_path = tmp_path / "kb.pkl"

    output = run_cli(monkeypatch, capsys, "ingest", *two_folders, "--index", str(index_path))

    assert output == f"Indexed 2 passages into {index_path}\n"
    assert index_path.exists()


def test_retrieve_reads_a_saved_index(monkeypatch, capsys, two_folders: list[str], tmp_path: Path):
    index_path = str(tmp_path / "kb.pkl")
    run_cli(monkeypatch, capsys, "ingest", *two_folders, "--index", index_path)

    output = run_cli(monkeypatch, capsys, "retrieve", "password", "--index", index_path, "--top-k", "1")

    assert "faq.md#1" in output
    assert "Reset your password from the login page." in output
    assert "refunds.md#1" not in output


def test_search_reads_a_saved_index(monkeypatch, capsys, two_folders: list[str], tmp_path: Path):
    index_path = str(tmp_path / "kb.pkl")
    run_cli(monkeypatch, capsys, "ingest", *two_folders, "--index", index_path)

    output = run_cli(monkeypatch, capsys, "search", "refunds", "--index", index_path)

    assert "refunds.md#1" in output


def test_retrieve_reports_when_nothing_matches(monkeypatch, capsys, two_folders: list[str], tmp_path: Path):
    index_path = str(tmp_path / "kb.pkl")
    run_cli(monkeypatch, capsys, "ingest", *two_folders, "--index", index_path)

    assert run_cli(monkeypatch, capsys, "retrieve", "zebra", "--index", index_path) == "No passages matched.\n"


def test_dataset_and_index_cannot_be_combined(monkeypatch, capsys, tmp_path: Path):
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, capsys, "search", "x", "--dataset", "a.json", "--index", str(tmp_path / "kb.pkl"))


def test_missing_extra_exits_with_its_install_hint(monkeypatch, capsys, tmp_path: Path):
    (tmp_path / "manual.pdf").write_bytes(b"%PDF-1.4")

    def raise_missing_extra(module_name: str):
        raise ImportError(MISSING_FORMATS_EXTRA)

    monkeypatch.setattr("recall_engine.sources.files.import_formats_module", raise_missing_extra)

    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, capsys, "ingest", str(tmp_path), "--index", str(tmp_path / "kb.pkl"))

    assert exit_info.value.code == f"Error: {MISSING_FORMATS_EXTRA}"


def test_ingest_saves_a_database_url_but_skips_embedding_it(monkeypatch, capsys, sqlite_path: Path, tmp_path: Path):
    index_path = tmp_path / "kb.pkl"

    output = run_cli(monkeypatch, capsys, "ingest", f"sqlite:///{sqlite_path}", "--index", str(index_path), "--embed")

    assert output.splitlines() == [
        f"Indexed 3 passages into {index_path}",
        "Skipped --embed: embeddings are cached by source fingerprint, and a database URL source has none",
    ]
    assert index_path.exists()
