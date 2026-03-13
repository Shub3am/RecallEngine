from __future__ import annotations

import math
from typing import Any


class RankedRetrieval:
    """Readable ranked retrieval helper for BM25 and TF-IDF."""

    def __init__(
        self,
        doc_map: dict[str, dict[str, str]],
        term_frequencies: dict[str, dict[str, int]],
        document_frequencies: dict[str, int],
        document_lengths: dict[str, int],
        total_documents: int,
        average_document_length: float,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.doc_map = doc_map
        self.term_frequencies = term_frequencies
        self.document_frequencies = document_frequencies
        self.document_lengths = document_lengths
        self.total_documents = total_documents
        self.average_document_length = average_document_length
        self.k1 = k1
        self.b = b

    def _candidate_doc_ids(self, query_terms: list[str]) -> set[str]:
        candidate_ids: set[str] = set()
        for term in query_terms:
            candidate_ids.update(self.term_frequencies.get(term, {}).keys())
        return candidate_ids

    def _tfidf_idf(self, term: str) -> float:
        df = self.document_frequencies.get(term, 0)
        if df == 0 or self.total_documents == 0:
            return 0.0
        return math.log(self.total_documents / df)

    def _bm25_idf(self, term: str) -> float:
        df = self.document_frequencies.get(term, 0)
        if df == 0 or self.total_documents == 0:
            return 0.0
        return math.log(1 + ((self.total_documents - df + 0.5) / (df + 0.5)))

    def score_tfidf(self, query_terms: list[str]) -> dict[str, float]:
        candidate_ids = self._candidate_doc_ids(query_terms)
        scores: dict[str, float] = {}

        for doc_id in candidate_ids:
            score = 0.0
            for term in query_terms:
                tf = self.term_frequencies.get(term, {}).get(doc_id, 0)
                if tf == 0:
                    continue
                score += tf * self._tfidf_idf(term)
            if score > 0:
                scores[doc_id] = score

        return scores

    def score_bm25(self, query_terms: list[str]) -> dict[str, float]:
        candidate_ids = self._candidate_doc_ids(query_terms)
        scores: dict[str, float] = {}

        for doc_id in candidate_ids:
            score = 0.0
            doc_length = self.document_lengths.get(doc_id, 0)
            for term in query_terms:
                tf = self.term_frequencies.get(term, {}).get(doc_id, 0)
                if tf == 0:
                    continue

                idf = self._bm25_idf(term)
                length_norm = 1 - self.b + self.b * (doc_length / self.average_document_length) if self.average_document_length else 1.0
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * length_norm
                score += idf * (numerator / denominator)

            if score > 0:
                scores[doc_id] = score

        return scores

    def rank(self, query_terms: list[str], method: str = "bm25", top_k: int | None = None) -> list[dict[str, Any]]:
        # This method assumes the query has already been normalized by the
        # caller. Keeping normalization outside this class separates corpus
        # statistics from query parsing concerns.
        if method == "tfidf":
            scores = self.score_tfidf(query_terms)
        elif method == "bm25":
            scores = self.score_bm25(query_terms)
        else:
            raise ValueError("method must be one of: bm25, tfidf")

        ranked_doc_ids = sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))
        if top_k is not None:
            ranked_doc_ids = ranked_doc_ids[:top_k]

        ranked_results: list[dict[str, Any]] = []
        for rank_position, doc_id in enumerate(ranked_doc_ids, start=1):
            document = dict(self.doc_map[doc_id])
            document["score"] = scores[doc_id]
            document["rank"] = rank_position
            ranked_results.append(document)

        return ranked_results