"""Answers a question from retrieved passages with Claude, citing the passages it used.

Must not search, index or load documents; the caller hands in the passages.
"""

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
        try:
            import anthropic
        except ImportError as error:
            raise ImportError(MISSING_RAG_EXTRA) from error
        client = anthropic.Anthropic()

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
    cited_passage_ids: list[str] = []
    citations: list[dict[str, Any]] = []
    # The response can also hold thinking or fallback blocks; only text blocks carry the answer.
    for block in response.content:
        if block.type != "text":
            continue
        markers = []
        for citation in block.citations or []:
            passage_id = passages[citation.document_index][0]
            if passage_id not in cited_passage_ids:
                cited_passage_ids.append(passage_id)
                citations.append(
                    {
                        "number": len(cited_passage_ids),
                        "passage_id": passage_id,
                        "cited_text": citation.cited_text,
                    }
                )
            marker = f"[{cited_passage_ids.index(passage_id) + 1}]"
            if marker not in markers:
                markers.append(marker)
        answer_parts.append(block.text + "".join(markers))

    return {"question": question, "answer": "".join(answer_parts).strip(), "citations": citations}
