import json
from pathlib import Path
from typing import Any

from recall_engine.search_engine.evaluator import Evaluator
from recall_engine.search_engine.indexer import Indexer
from recall_engine.search_engine.lexer import Lexer
from recall_engine.search_engine.parser import Parser
from recall_engine.search_engine.ranked_retrieval import RankedRetrieval
from recall_engine.search_engine.tokenizer import Tokenizer

SEARCH_MODES = ("auto", "keyword", "boolean", "bm25", "tfidf", "semantic", "hybrid")
RANKED_MODES = {"bm25", "tfidf", "semantic", "hybrid"}

# Reciprocal Rank Fusion constant from Cormack et al. (2009); 60 damps the
# influence of any single ranking's top positions.
RRF_K = 60
HYBRID_CANDIDATE_POOL = 100


class SearchEngine:
    """Library-first search facade over keyword, boolean, ranked, semantic and hybrid retrieval."""

    def __init__(
        self,
        indexer: Indexer | None = None,
        tokenizer: Tokenizer | None = None,
        embedding_model: Any | None = None,
    ) -> None:
        self.indexer = indexer if indexer is not None else Indexer(tokenizer=tokenizer)
        self.tokenizer = tokenizer if tokenizer is not None else self.indexer.tokenizer
        self.embedding_model = embedding_model
        self._semantic_retrieval: Any | None = None

    @classmethod
    def from_json(
        cls,
        doc_path: str,
        data_key: str = "",
        doc_id_key: str = "id",
        exclude_doc_keys: list[str] | None = None,
        cache_path: str | None = None,
        embedding_model: Any | None = None,
    ) -> "SearchEngine":
        engine = cls(indexer=Indexer(file_path=cache_path), embedding_model=embedding_model)
        engine.load_or_build_index(
            doc_path=doc_path,
            data_key=data_key,
            doc_id_key=doc_id_key,
            exclude_doc_keys=exclude_doc_keys,
        )
        return engine

    @classmethod
    def from_documents(
        cls,
        documents: list[dict[str, Any]],
        doc_id_key: str = "id",
        exclude_doc_keys: list[str] | None = None,
        embedding_model: Any | None = None,
    ) -> "SearchEngine":
        engine = cls(embedding_model=embedding_model)
        engine.indexer.build_from_documents(documents, docIdKey=doc_id_key, excludeDocKeys=exclude_doc_keys)
        return engine

    def build_index(
        self,
        doc_path: str,
        data_key: str = "",
        doc_id_key: str = "id",
        exclude_doc_keys: list[str] | None = None,
        persist: bool = True,
    ) -> None:
        self._semantic_retrieval = None
        self.indexer.build(
            docPath=doc_path,
            dataKey=data_key,
            docIdKey=doc_id_key,
            excludeDocKeys=exclude_doc_keys,
        )
        if persist:
            self.indexer.save()

    def load_index(self, force: bool = False) -> None:
        self._semantic_retrieval = None
        self.indexer.load(force=force)

    def load_or_build_index(
        self,
        doc_path: str,
        data_key: str = "",
        doc_id_key: str = "id",
        exclude_doc_keys: list[str] | None = None,
    ) -> None:
        self._semantic_retrieval = None
        self.indexer.load_or_build(
            docPath=doc_path,
            dataKey=data_key,
            docIdKey=doc_id_key,
            excludeDocKeys=exclude_doc_keys,
        )

    def search(self, query: str, mode: str = "auto", top_k: int | None = None) -> list[dict[str, Any]]:
        selected_mode = self._resolve_mode(query, mode)
        self._validate_top_k(top_k)
        if selected_mode == "boolean":
            return self._search_boolean(query)
        if selected_mode in {"bm25", "tfidf"}:
            return self._search_ranked(query, method=selected_mode, top_k=top_k)
        if selected_mode == "semantic":
            return self._as_ranked_documents(self._get_semantic_retrieval().rank(query, top_k))
        if selected_mode == "hybrid":
            return self._search_hybrid(query, top_k)
        return self._search_keyword(query)

    def _resolve_mode(self, query: str, mode: str) -> str:
        if mode not in SEARCH_MODES:
            raise ValueError(f"mode must be one of: {', '.join(SEARCH_MODES)}")
        if mode != "auto":
            return mode

        upper_query = query.upper()
        operators = (" AND ", " OR ", "NOT ", "(", ")")
        return "boolean" if any(op in upper_query for op in operators) else "keyword"

    def _search_keyword(self, query: str) -> list[dict[str, Any]]:
        return self.indexer.get_documents(query)

    def _search_boolean(self, query: str) -> list[dict[str, Any]]:
        tokens = Lexer(query).tokens
        ast = Parser().parse(tokens)
        doc_map = self.indexer.get_doc_map()
        evaluator = Evaluator(self.indexer.get_index(), doc_map, tokenizer=self.tokenizer)
        doc_ids = evaluator.evaluate(ast)
        return [doc_map[doc_id] for doc_id in sorted(doc_ids) if doc_id in doc_map]

    def _ranked_retrieval(self) -> RankedRetrieval:
        return RankedRetrieval(
            self.indexer.get_doc_map(),
            self.indexer.get_term_frequencies(),
            self.indexer.get_document_frequencies(),
            self.indexer.get_document_lengths(),
            self.indexer.get_total_documents(),
            self.indexer.get_average_document_length(),
        )

    def _search_ranked(self, query: str, method: str, top_k: int | None = None) -> list[dict[str, Any]]:
        query_terms = self.tokenizer.tokenize_with_frequency(query)
        return self._ranked_retrieval().rank(query_terms, method=method, top_k=top_k)

    def _search_hybrid(self, query: str, top_k: int | None) -> list[dict[str, Any]]:
        bm25_scores = self._ranked_retrieval().score_bm25(self.tokenizer.tokenize_with_frequency(query))
        bm25_ranking = sorted(bm25_scores, key=lambda doc_id: (-bm25_scores[doc_id], doc_id))[:HYBRID_CANDIDATE_POOL]
        semantic_ranking = [doc_id for doc_id, _ in self._get_semantic_retrieval().rank(query, HYBRID_CANDIDATE_POOL)]

        fused_scores: dict[str, float] = {}
        for ranking in (bm25_ranking, semantic_ranking):
            for position, doc_id in enumerate(ranking, start=1):
                fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1 / (RRF_K + position)

        fused_ranking = sorted(fused_scores.items(), key=lambda item: (-item[1], item[0]))
        return self._as_ranked_documents(fused_ranking[:top_k])

    def _as_ranked_documents(self, scored_doc_ids: list[tuple[str, float]]) -> list[dict[str, Any]]:
        ranked_documents = []
        for rank_position, (doc_id, score) in enumerate(scored_doc_ids, start=1):
            document = dict(self.indexer.get_doc_map()[doc_id])
            document["score"] = score
            document["rank"] = rank_position
            ranked_documents.append(document)
        return ranked_documents

    def _get_semantic_retrieval(self) -> Any:
        if self._semantic_retrieval is not None:
            return self._semantic_retrieval

        # Imported here so keyword-only installs never need numpy or fastembed.
        from recall_engine.search_engine.semantic_retrieval import (
            SemanticRetrieval,
            embedding_model_name,
            load_default_embedding_model,
        )

        if self.embedding_model is None:
            self.embedding_model = load_default_embedding_model()

        source_fingerprint = self.indexer.source_fingerprint
        embeddings_cache_path = Path(self.indexer.default_file_path).with_suffix(".embeddings.npz")
        cache_key = json.dumps(
            {"source": source_fingerprint, "model": embedding_model_name(self.embedding_model)}, sort_keys=True
        )

        semantic_retrieval = None
        if source_fingerprint is not None:
            semantic_retrieval = SemanticRetrieval.load(self.embedding_model, embeddings_cache_path, cache_key)
        if semantic_retrieval is None:
            document_texts = {doc_id: self.indexer.get_document_text(doc_id) for doc_id in self.indexer.get_doc_map()}
            semantic_retrieval = SemanticRetrieval.from_documents(self.embedding_model, document_texts)
            if source_fingerprint is not None:
                semantic_retrieval.save(embeddings_cache_path, cache_key)

        self._semantic_retrieval = semantic_retrieval
        return semantic_retrieval

    def _validate_top_k(self, top_k: int | None) -> None:
        if top_k is None:
            return
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer")


def build_engine(doc_path: str, data_key: str = "movies") -> SearchEngine:
    """Convenience function for one-call setup from a JSON dataset."""
    engine = SearchEngine()
    engine.load_or_build_index(doc_path=doc_path, data_key=data_key)
    return engine
