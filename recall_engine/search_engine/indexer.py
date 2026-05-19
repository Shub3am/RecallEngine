import json
import pickle
from pathlib import Path
from typing import Any

from recall_engine.search_engine.tokenizer import Tokenizer


class Indexer:
    """Inverted index for efficient document retrieval by terms."""

    def __init__(
        self,
        document_index: dict[str, list[str]] | None = None,
        document_map: dict[str, dict[str, str]] | None = None,
        term_frequencies: dict[str, dict[str, int]] | None = None,
        document_frequencies: dict[str, int] | None = None,
        document_lengths: dict[str, int] | None = None,
        total_documents: int = 0,
        average_document_length: float = 0.0,
        file_path: str | None = None,
        tokenizer: Tokenizer | None = None,
    ) -> None:
        self.index = document_index if document_index is not None else {}
        self.doc_map = document_map if document_map is not None else {}
        self.term_frequencies = term_frequencies if term_frequencies is not None else {}
        self.document_frequencies = document_frequencies if document_frequencies is not None else {}
        self.document_lengths = document_lengths if document_lengths is not None else {}
        self.total_documents = total_documents
        self.average_document_length = average_document_length
        self.default_file_path = file_path or str(self._default_cache_path())
        self.tokenizer = tokenizer if tokenizer is not None else Tokenizer()

    @staticmethod
    def _default_cache_path() -> Path:
        return Path(__file__).resolve().parents[1] / "cache" / "cache.pkl"

    @staticmethod
    def _dataset_loader_json(file_name_with_dir: str) -> dict[str, dict[str|int, str|int]] | list[str|int]:
        with open(file_name_with_dir, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_index(self) -> dict[str, list[str]]:
        return self.index

    def get_doc_map(self) -> dict[str, dict[str, str]]:
        return self.doc_map

    def get_term_frequencies(self) -> dict[str, dict[str, int]]:
        return self.term_frequencies

    def get_document_frequencies(self) -> dict[str, int]:
        return self.document_frequencies

    def get_document_lengths(self) -> dict[str, int]:
        return self.document_lengths

    def get_total_documents(self) -> int:
        return self.total_documents

    def get_average_document_length(self) -> float:
        return self.average_document_length

    def __add_document(self, doc_id: str, text: str) -> None:
        # The boolean/keyword index only needs unique normalized terms.
        for token in self.tokenizer.tokenize(text):
            self.index.setdefault(token, []).append(doc_id)

        # Ranked retrieval also needs repeated terms so tf(t, d) is correct.
        frequency_tokens = self.tokenizer.tokenize_with_frequency(text)
        self.document_lengths[doc_id] = len(frequency_tokens)

        unique_terms: set[str] = set()
        for token in frequency_tokens:
            postings = self.term_frequencies.setdefault(token, {})
            postings[doc_id] = postings.get(doc_id, 0) + 1
            unique_terms.add(token)

        for token in unique_terms:
            self.document_frequencies[token] = self.document_frequencies.get(token, 0) + 1

    def build(
        self,
        docPath: str,
        dataKey: str = "",
        docIdKey: str = "id",
        excludeDocKeys: list[str] | None = None,
    ) -> None:
        exclude_keys = set(excludeDocKeys if excludeDocKeys is not None else ["id"])
        data = self._dataset_loader_json(docPath)

        if dataKey:
            if not isinstance(data, dict) or dataKey not in data:
                raise ValueError(f"dataKey '{dataKey}' not present in dataset")
            documents = data[dataKey]
        else:
            documents = data

        if not isinstance(documents, list):
            raise ValueError("Dataset must be a list of documents")

        self.index = {}
        self.doc_map = {}
        self.term_frequencies = {}
        self.document_frequencies = {}
        self.document_lengths = {}
        self.total_documents = 0
        self.average_document_length = 0.0

        for doc in documents:
            if not isinstance(doc, dict):
                continue
            if docIdKey not in doc:
                continue
            doc_id = str(doc[docIdKey])
            text_parts = [str(value) for key, value in doc.items() if key not in exclude_keys]
            self.doc_map[doc_id] = doc  # type: ignore[assignment]
            self.__add_document(doc_id, " ".join(text_parts))

        self.total_documents = len(self.doc_map)
        total_length = sum(self.document_lengths.values())
        if self.total_documents > 0:
            self.average_document_length = total_length / self.total_documents

    def save(self, filepath: str = "") -> None:
        path = filepath or self.default_file_path
        os_path = Path(path)
        os_path.parent.mkdir(parents=True, exist_ok=True)
        with os_path.open("wb") as file:
            pickle.dump(
                {
                    "version": 2,
                    "index": self.index,
                    "doc_map": self.doc_map,
                    "term_frequencies": self.term_frequencies,
                    "document_frequencies": self.document_frequencies,
                    "document_lengths": self.document_lengths,
                    "total_documents": self.total_documents,
                    "average_document_length": self.average_document_length,
                },
                file,
            )

    def load(self, filepath: str = "", force: bool = False) -> None:
        if self.doc_map and self.index and not force:
            raise RuntimeError("Index and document map are already populated. Use force=True to reload.")

        path = Path(filepath or self.default_file_path)
        if not path.exists():
            raise FileNotFoundError(f"Index file not found at {path}")

        try:
            with path.open("rb") as file:
                data = pickle.load(file)
        except pickle.UnpicklingError as exc:
            raise ValueError(f"Failed to load index: corrupted file. {exc}") from exc

        try:
            self.index = data["index"]
            self.doc_map = data["doc_map"]
        except KeyError as exc:
            raise ValueError(f"Invalid index file: missing key {exc}") from exc

        if self._has_ranking_stats(data):
            self.term_frequencies = data["term_frequencies"]
            self.document_frequencies = data["document_frequencies"]
            self.document_lengths = data["document_lengths"]
            self.total_documents = data["total_documents"]
            self.average_document_length = data["average_document_length"]
        else:
            # Backward-compatible fallback for older cache files.
            self._rebuild_ranking_stats_from_doc_map()

    def load_or_build(
        self,
        docPath: str,
        dataKey: str = "",
        docIdKey: str = "id",
        excludeDocKeys: list[str] | None = None,
    ) -> None:
        try:
            self.load()
        except (FileNotFoundError, ValueError):
            self.build(docPath, dataKey=dataKey, docIdKey=docIdKey, excludeDocKeys=excludeDocKeys)
            self.save()

    def _has_ranking_stats(self, data: dict[str, Any]) -> bool:
        required_keys = {
            "term_frequencies",
            "document_frequencies",
            "document_lengths",
            "total_documents",
            "average_document_length",
        }
        return required_keys.issubset(data)

    def _rebuild_ranking_stats_from_doc_map(self) -> None:
        self.term_frequencies = {}
        self.document_frequencies = {}
        self.document_lengths = {}

        for doc_id, document in self.doc_map.items():
            text = " ".join(str(value) for key, value in document.items() if key != "id")
            frequency_tokens = self.tokenizer.tokenize_with_frequency(text)
            self.document_lengths[doc_id] = len(frequency_tokens)

            unique_terms: set[str] = set()
            for token in frequency_tokens:
                postings = self.term_frequencies.setdefault(token, {})
                postings[doc_id] = postings.get(doc_id, 0) + 1
                unique_terms.add(token)

            for token in unique_terms:
                self.document_frequencies[token] = self.document_frequencies.get(token, 0) + 1

        self.total_documents = len(self.doc_map)
        total_length = sum(self.document_lengths.values())
        self.average_document_length = (total_length / self.total_documents) if self.total_documents else 0.0

    def get_documents(self, terms: str | list[str], operation: str = "OR") -> list[dict[str, str]]:
        raw_terms = [terms] if isinstance(terms, str) else terms
        normalized_terms: list[str] = []
        for term in raw_terms:
            normalized_terms.extend(self.tokenizer.tokenize(term))

        if not normalized_terms:
            return []

        op = operation.upper() if operation else "OR"
        if op == "AND":
            matched_ids: set[str] | None = None
            for token in normalized_terms:
                token_ids = set(self.index.get(token, []))
                if matched_ids is None:
                    matched_ids = token_ids
                else:
                    matched_ids &= token_ids
                if not matched_ids:
                    break
            resolved_ids = matched_ids if matched_ids is not None else set()
        elif op == "NOT":
            resolved_ids = set(self.index.get(normalized_terms[0], []))
            if len(normalized_terms) > 1:
                excluded: set[str] = set()
                for token in normalized_terms[1:]:
                    excluded.update(self.index.get(token, []))
                resolved_ids -= excluded
        else:
            resolved_ids: set[str] = set()
            for token in normalized_terms:
                resolved_ids.update(self.index.get(token, []))

        return [self.doc_map[doc_id] for doc_id in sorted(resolved_ids) if doc_id in self.doc_map]
