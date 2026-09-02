"""Answers a question from retrieved passages with Claude, citing the passages it used.

Must not search, index or load documents; the caller hands in the passages.
"""

import functools
from typing import Any

DEFAULT_MODEL = "claude-opus-5-5"
MAX_ANSWER_TOKENS = 16000
SERVER_SIDE_FALLBACK_BETA = "server-side-fallback-2026-07-01"
MISSING_RAG_EXTRA = 'Answering questions needs the optional extra: pip install "recall-engine[rag]"'

SYSTEM_PROMPT = (
    "Answer the user's question using only the documents provided. "
    "If the documents do not contain the answer, say so plainly instead of guessing. "
    "Keep the answer short and direct."
)


def answer_question(
    question: str,
    passages: list[tuple[str, str]],
    client: Any | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Answer `question` from `(passage_id, passage_text)` pairs; citations point back to passage ids."""
    if client is None:
        client = _default_client()

    # Documents go before the question: Claude answers long-context prompts best when the question comes last.
    content: list[dict[str, Any]] = [
        {
            "type": "document",
            "source": {"type": "text", "media_type": "text/plain", "data": passage_text},
            "title": passage_id,
            "citations": {"enabled": True},
        }
        for passage_id, passage_text in passages
    ]
    content.append({"type": "text", "text": question})

    response = client.beta.messages.create(
        model=model,
        max_tokens=MAX_ANSWER_TOKENS,
        betas=[SERVER_SIDE_FALLBACK_BETA],
        fallbacks="default",
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to answer this question.")

    answer_parts: list[str] = []
    citation_number_by_passage_id: dict[str, int] = {}
    citations: list[dict[str, Any]] = []
    # The response can also hold thinking or fallback blocks; only text blocks carry the answer.
    for block in response.content:
        if block.type != "text":
            continue
        block_markers: dict[str, None] = {}
        for citation in block.citations or []:
            passage_id = passages[citation.document_index][0]
            if passage_id not in citation_number_by_passage_id:
                citation_number_by_passage_id[passage_id] = len(citations) + 1
                citations.append(
                    {"number": len(citations) + 1, "passage_id": passage_id, "cited_text": citation.cited_text}
                )
            block_markers[f"[{citation_number_by_passage_id[passage_id]}]"] = None
        answer_parts.append(block.text + "".join(block_markers))

    return {"question": question, "answer": "".join(answer_parts).strip(), "citations": citations}


# One client per process so repeated questions reuse its HTTP connection pool.
@functools.cache
def _default_client() -> Any:
    try:
        import anthropic
    except ImportError as error:
        raise ImportError(MISSING_RAG_EXTRA) from error
    return anthropic.Anthropic()
