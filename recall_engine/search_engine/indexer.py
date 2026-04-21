import json
import pickle
from pathlib import Path

from recall_engine.search_engine.tokenizer import Tokenizer


class Indexer:
    """Inverted index for efficient document retrieval by terms."""

    def __init__(
        self,
        document_index: dict[str, list[str]] | None = None,
        document_map: dict[str, dict[str, str]] | None = None,
        file_path: str | None = None,
        tokenizer: Tokenizer | None = None,
    ) -> None:
        self.index = document_index if document_index is not None else {}
        self.doc_map = document_map if document_map is not None else {}
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

    def __add_document(self, doc_id: str, text: str) -> None:
        tokens = self.tokenizer.tokenize(text)
        for token in tokens:
            self.index.setdefault(token, [])
            if doc_id not in self.index[token]:
                self.index[token].append(doc_id)

    def build(
        self,
        docPath: str,
        dataKey: str = "",
        docIdKey: str = "id",
        excludeDocKeys: list[str] | None = None,
    ) -> None:
        exclude_keys = excludeDocKeys if excludeDocKeys is not None else ["id"]
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

        for doc in documents:
            if not isinstance(doc, dict):
                continue
            if docIdKey not in doc:
                continue
            doc_id = str(doc[docIdKey])
            text_parts: list[str] = []
            for key, value in doc.items():
                if key not in exclude_keys:
                    text_parts.append(str(value))
            self.doc_map[doc_id] = doc  # type: ignore[assignment]
            self.__add_document(doc_id, " ".join(text_parts).strip())

    def save(self, filepath: str = "") -> None:
        path = filepath or self.default_file_path
        os_path = Path(path)
        os_path.parent.mkdir(parents=True, exist_ok=True)
        with os_path.open("wb") as file:
            pickle.dump({"index": self.index, "doc_map": self.doc_map}, file)

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

    def get_documents(self, terms: str | list[str], operation: str = "OR") -> list[dict[str, str]]:
        raw_terms = [terms] if isinstance(terms, str) else terms
        normalized_terms: list[str] = []
        for term in raw_terms:
            normalized_terms.extend(self.tokenizer.tokenize(term))

        if not normalized_terms:
            return []

        op = operation.upper() if operation else "OR"
        term_sets = [set(self.index.get(token, [])) for token in normalized_terms]

        if op == "AND":
            matched_ids = term_sets[0].copy()
            for ids in term_sets[1:]:
                matched_ids &= ids
        elif op == "NOT":
            matched_ids = term_sets[0].copy()
            excluded = set().union(*term_sets[1:]) if len(term_sets) > 1 else set()
            matched_ids -= excluded
        else:
            matched_ids = set().union(*term_sets)

        return [self.doc_map[doc_id] for doc_id in sorted(matched_ids) if doc_id in self.doc_map]
