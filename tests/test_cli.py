from pathlib import Path

import pytest

from recall_engine.cli.main import cli
from tests.test_rag_pipeline import write_folder

#Test Command: uv run pytest tests/test_cli.py -v


def run_cli(monkeypatch, capsys, *arguments: str) -> str:
    monkeypatch.setattr("sys.argv", ["recall_engine", *arguments])
    cli()
    return capsys.readouterr().out


@pytest.fixture
def knowledge_base(tmp_path: Path) -> list[str]:
    policies = write_folder(tmp_path / "policies", {"refunds.md": "Refunds are paid within 14 days."})
    support = write_folder(tmp_path / "support", {"faq.md": "Reset your password from the login page."})
    return [str(policies), str(support)]


def test_ingest_saves_one_index_from_several_sources(monkeypatch, capsys, knowledge_base: list[str], tmp_path: Path):
    index_path = tmp_path / "kb.pkl"

    output = run_cli(monkeypatch, capsys, "ingest", *knowledge_base, "--index", str(index_path))

    assert output == f"Indexed 2 passages into {index_path}\n"
    assert index_path.exists()


def test_retrieve_reads_a_saved_index(monkeypatch, capsys, knowledge_base: list[str], tmp_path: Path):
    index_path = str(tmp_path / "kb.pkl")
    run_cli(monkeypatch, capsys, "ingest", *knowledge_base, "--index", index_path)

    output = run_cli(monkeypatch, capsys, "retrieve", "password", "--index", index_path, "--top-k", "1")

    assert "faq.md#1" in output
    assert "Reset your password from the login page." in output
    assert "refunds.md#1" not in output


def test_search_reads_a_saved_index(monkeypatch, capsys, knowledge_base: list[str], tmp_path: Path):
    index_path = str(tmp_path / "kb.pkl")
    run_cli(monkeypatch, capsys, "ingest", *knowledge_base, "--index", index_path)

    output = run_cli(monkeypatch, capsys, "search", "refunds", "--index", index_path)

    assert "refunds.md#1" in output


def test_retrieve_reports_when_nothing_matches(monkeypatch, capsys, knowledge_base: list[str], tmp_path: Path):
    index_path = str(tmp_path / "kb.pkl")
    run_cli(monkeypatch, capsys, "ingest", *knowledge_base, "--index", index_path)

    assert run_cli(monkeypatch, capsys, "retrieve", "zebra", "--index", index_path) == "No passages matched.\n"


def test_dataset_and_index_cannot_be_combined(monkeypatch, capsys, tmp_path: Path):
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, capsys, "search", "x", "--dataset", "a.json", "--index", str(tmp_path / "kb.pkl"))
