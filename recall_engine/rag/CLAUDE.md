# rag

## Owns

Turning a question plus retrieved passages into a short answer from Claude, with numbered citations that point back to passage ids.

## Must not know about

Indexing, search modes, file formats, HTTP or argparse. The caller retrieves the passages; this module only calls Claude.

## Entry points

- `answer_question(question, passages, client=None, model=...)`: `passages` is a list of `(passage_id, passage_text)`. Returns `{"question", "answer", "citations": [{"number", "passage_id", "cited_text"}]}`.

## Invariants and gotchas

- `anthropic` is imported lazily, only when no `client` is passed. Missing it raises `ImportError` naming the `rag` extra.
- Without a `client`, `anthropic.Anthropic()` reads `ANTHROPIC_API_KEY` from the environment.
- Each passage is sent as a text document with citations enabled and the passage id as its title. Citation `document_index` is the position in `passages`, so the order of `passages` must not change between building the request and reading the response.
- Citation numbers follow first appearance in the answer, not retrieval rank. `[n]` markers are appended after the text block that cited them.
- Only `text` blocks are read; thinking and fallback blocks are skipped. `stop_reason == "refusal"` raises `RuntimeError`.
- Citations are incompatible with structured outputs (`output_config.format`); do not add one.
- Uses the beta endpoint for server-side fallback (`SERVER_SIDE_FALLBACK_BETA`), so an overloaded primary model falls back instead of failing.

## Called by

`SearchEngine.ask` in `recall_engine/search_engine/engine.py`, and the tests with a fake client.
