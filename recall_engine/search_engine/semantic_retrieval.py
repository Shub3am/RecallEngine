"""Ranks documents by embedding similarity to a query.

Exists so meaning-based retrieval stays optional: it is only imported when a
semantic or hybrid search runs. Must not know about the inverted index, search
modes, or where the cache file lives; callers pass texts, paths and cache keys.
"""
from pathlib import Path
from typing import Any

MISSING_SEMANTIC_EXTRA = 'Semantic and hybrid search need the optional extra: pip install "recall-engine[semantic]"'
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

try:
    import numpy as np
except ImportError as exc:
    raise ImportError(MISSING_SEMANTIC_EXTRA) from exc


def load_default_embedding_model() -> Any:
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise ImportError(MISSING_SEMANTIC_EXTRA) from exc
    # fastembed downloads the ONNX model (~70 MB) on first use and reuses its local copy afterwards.
    return TextEmbedding(model_name=DEFAULT_EMBEDDING_MODEL)


def embedding_model_name(embedding_model: Any) -> str:
    return str(getattr(embedding_model, "model_name", type(embedding_model).__name__))


def _normalize_rows(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


class SemanticRetrieval:
    def __init__(self, embedding_model: Any, doc_ids: list[str], document_embeddings: np.ndarray) -> None:
        self.embedding_model = embedding_model
        self.doc_ids = doc_ids
        self.document_embeddings = _normalize_rows(np.asarray(document_embeddings, dtype=np.float32))

    @classmethod
    def from_documents(cls, embedding_model: Any, document_texts: dict[str, str]) -> "SemanticRetrieval":
        doc_ids = list(document_texts)
        embeddings = list(embedding_model.passage_embed([document_texts[doc_id] for doc_id in doc_ids]))
        return cls(embedding_model, doc_ids, np.array(embeddings) if embeddings else np.zeros((0, 1)))

    @classmethod
    def load(cls, embedding_model: Any, cache_path: Path, cache_key: str) -> "SemanticRetrieval | None":
        if not cache_path.exists():
            return None
        with np.load(cache_path, allow_pickle=False) as cached:
            if str(cached["cache_key"]) != cache_key:
                return None
            return cls(embedding_model, [str(doc_id) for doc_id in cached["doc_ids"]], cached["embeddings"])

    def save(self, cache_path: Path, cache_key: str) -> None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # np.savez appends .npz unless the path already ends with it, so write through a file handle.
        with cache_path.open("wb") as cache_file:
            np.savez(
                cache_file,
                cache_key=np.array(cache_key),
                doc_ids=np.array(self.doc_ids),
                embeddings=self.document_embeddings,
            )

    def rank(self, query: str, top_k: int | None = None) -> list[tuple[str, float]]:
        if not self.doc_ids:
            return []
        query_embedding = _normalize_rows(np.asarray(next(iter(self.embedding_model.query_embed(query))), dtype=np.float32))
        similarities = self.document_embeddings @ query_embedding
        ranked_positions = np.argsort(-similarities, kind="stable")[:top_k]
        return [(self.doc_ids[position], float(similarities[position])) for position in ranked_positions]
