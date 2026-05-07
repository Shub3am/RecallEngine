from recall_engine.search_engine.evaluator import Evaluator
from recall_engine.search_engine.indexer import Indexer
from recall_engine.search_engine.lexer import Lexer
from recall_engine.search_engine.parser import Parser
from recall_engine.search_engine.ranked_retrieval import RankedRetrieval
from recall_engine.search_engine.tokenizer import Tokenizer


class SearchEngine:
    """Library-first search facade that supports keyword and boolean queries."""

    def __init__(self, indexer: Indexer | None = None, tokenizer: Tokenizer | None = None) -> None:
        self.indexer = indexer if indexer is not None else Indexer(tokenizer=tokenizer)
        self.tokenizer = tokenizer if tokenizer is not None else self.indexer.tokenizer

    def build_index(
        self,
        doc_path: str,
        data_key: str = "",
        doc_id_key: str = "id",
        exclude_doc_keys: list[str] | None = None,
        persist: bool = True,
    ) -> None:
        self.indexer.build(
            docPath=doc_path,
            dataKey=data_key,
            docIdKey=doc_id_key,
            excludeDocKeys=exclude_doc_keys,
        )
        if persist:
            self.indexer.save()

    def load_index(self, force: bool = False) -> None:
        self.indexer.load(force=force)

    def load_or_build_index(
        self,
        doc_path: str,
        data_key: str = "",
        doc_id_key: str = "id",
        exclude_doc_keys: list[str] | None = None,
    ) -> None:
        self.indexer.load_or_build(
            docPath=doc_path,
            dataKey=data_key,
            docIdKey=doc_id_key,
            excludeDocKeys=exclude_doc_keys,
        )

    def search(self, query: str, mode: str = "auto", top_k: int | None = None) -> list[dict[str, str]]:
        selected_mode = self._resolve_mode(query, mode)
        if selected_mode == "boolean":
            return self._search_boolean(query)
        if selected_mode in {"bm25", "tfidf"}:
            return self._search_ranked(query, method=selected_mode, top_k=top_k)
        return self._search_keyword(query)

    def _resolve_mode(self, query: str, mode: str) -> str:
        if mode not in {"auto", "keyword", "boolean", "bm25", "tfidf"}:
            raise ValueError("mode must be one of: auto, keyword, boolean, bm25, tfidf")
        if mode != "auto":
            return mode

        upper_query = query.upper()
        operators = (" AND ", " OR ", "NOT ", "(", ")")
        return "boolean" if any(op in upper_query for op in operators) else "keyword"

    def _search_keyword(self, query: str) -> list[dict[str, str]]:
        return self.indexer.get_documents(query)

    def _search_boolean(self, query: str) -> list[dict[str, str]]:
        tokens = Lexer(query).tokens
        ast = Parser().parse(tokens)
        doc_map = self.indexer.get_doc_map()
        evaluator = Evaluator(self.indexer.get_index(), doc_map, tokenizer=self.tokenizer)
        doc_ids = evaluator.evaluate(ast)
        return [doc_map[doc_id] for doc_id in sorted(doc_ids) if doc_id in doc_map]

    def _search_ranked(self, query: str, method: str, top_k: int | None = None) -> list[dict[str, str]]:
        ranked_retrieval = RankedRetrieval(
            self.indexer.get_index(),
            self.indexer.get_doc_map(),
            tokenizer=self.tokenizer,
        )
        return ranked_retrieval.rank(query, method=method, top_k=top_k)


def build_engine(doc_path: str, data_key: str = "movies") -> SearchEngine:
    """Convenience function for one-call setup from a JSON dataset."""
    engine = SearchEngine()
    engine.load_or_build_index(doc_path=doc_path, data_key=data_key)
    return engine
