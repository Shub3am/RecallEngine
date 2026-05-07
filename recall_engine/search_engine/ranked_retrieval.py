from __future__ import annotations

import math
from typing import Any

from recall_engine.search_engine.tokenizer import Tokenizer


class RankedRetrieval:
    """Simple first-draft ranked retrieval helper.

    This class intentionally favors readability over optimization so the ranking
    flow is easy to understand before we tune data structures later.
    """

    def __init__(
        self,
        index: dict[str, list[str]],
        doc_map: dict[str, dict[str, str]],
        tokenizer: Tokenizer | None = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        # We reuse the existing inverted index for fast candidate discovery.
        self.index = index
        self.doc_map = doc_map
        self.tokenizer = tokenizer if tokenizer is not None else Tokenizer()
        self.k1 = k1
        self.b = b

        # Ranking needs more statistics than boolean retrieval.
        # We compute them eagerly in this first draft so the logic stays simple.
        self.term_frequencies: dict[str, dict[str, int]] = {}
        self.document_frequencies: dict[str, int] = {}
        self.document_lengths: dict[str, int] = {}
        self.total_documents = len(self.doc_map)
        self.average_document_length = 0.0

        self._build_statistics()

    def _build_statistics(self) -> None:
        total_length = 0

        for doc_id, document in self.doc_map.items():
            # We exclude the document id from the searchable text because it is
            # an identifier, not natural language content.
            text = " ".join(str(value) for key, value in document.items() if key != "id")

            # Important: Tokenizer.tokenize() removes duplicates, which is okay
            # for boolean matching but incorrect for TF-based ranking. Here we
            # preserve repetitions so tf(t, d) remains meaningful.
            tokens = self._tokenize_with_frequency(text)
            self.document_lengths[doc_id] = len(tokens)
            total_length += len(tokens)

            unique_terms_in_document: set[str] = set()
            for token in tokens:
                postings = self.term_frequencies.setdefault(token, {})
                postings[doc_id] = postings.get(doc_id, 0) + 1
                unique_terms_in_document.add(token)

            for token in unique_terms_in_document:
                self.document_frequencies[token] = self.document_frequencies.get(token, 0) + 1

        if self.total_documents > 0:
            self.average_document_length = total_length / self.total_documents

    def _tokenize_with_frequency(self, content: str) -> list[str]:
        # This mirrors the existing normalization pipeline, but does not remove
        # repeated tokens because ranking must observe term frequency.
        normalized = content.lower()
        normalized = self.tokenizer._clean_punctuation(normalized)
        raw_tokens = normalized.split()
        filtered_tokens = self.tokenizer._remove_stop_words(raw_tokens)
        return [self.tokenizer.stemmer.stem(token, to_lowercase=True) for token in filtered_tokens]

    def _query_terms(self, query: str) -> list[str]:
        # Query-side ranking also needs repeated terms preserved for consistency.
        return self._tokenize_with_frequency(query)

    def _candidate_doc_ids(self, query_terms: list[str]) -> set[str]:
        # We only score documents that contain at least one query term.
        candidate_ids: set[str] = set()
        for term in query_terms:
            candidate_ids.update(self.index.get(term, []))
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

    def score_tfidf(self, query: str) -> dict[str, float]:
        query_terms = self._query_terms(query)
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

    def score_bm25(self, query: str) -> dict[str, float]:
        query_terms = self._query_terms(query)
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

    def rank(self, query: str, method: str = "bm25", top_k: int | None = None) -> list[dict[str, Any]]:
        # This is the user-facing convenience method: compute scores, sort them,
        # and attach the score to each returned document.
        if method == "tfidf":
            scores = self.score_tfidf(query)
        elif method == "bm25":
            scores = self.score_bm25(query)
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