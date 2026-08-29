from types import SimpleNamespace

import pytest

from recall_engine.rag import answer_question


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.request = None

    def create(self, **request):
        self.request = request
        return self.response


def fake_client(content, stop_reason="end_turn"):
    messages = FakeMessages(SimpleNamespace(stop_reason=stop_reason, content=content))
    return SimpleNamespace(beta=SimpleNamespace(messages=messages))


def text_block(text, citations=None):
    return SimpleNamespace(type="text", text=text, citations=citations)


def citation(document_index, cited_text):
    return SimpleNamespace(type="char_location", document_index=document_index, cited_text=cited_text)


PASSAGES = [
    ("notes.md#1", "The launch is on Friday."),
    ("notes.md#2", "The budget is 40k."),
]


def test_sends_each_passage_as_a_cited_document_before_the_question():
    client = fake_client([text_block("Friday.")])

    answer_question("When is the launch?", PASSAGES, client=client)

    request = client.beta.messages.request
    content = request["messages"][0]["content"]
    assert [block["type"] for block in content] == ["document", "document", "text"]
    assert content[0]["title"] == "notes.md#1"
    assert content[0]["source"]["data"] == "The launch is on Friday."
    assert content[0]["citations"] == {"enabled": True}
    assert content[-1]["text"] == "When is the launch?"
    assert request["model"] == "claude-opus-5-5"


def test_numbers_citations_by_first_appearance_and_marks_the_answer():
    client = fake_client(
        [
            text_block("The launch is Friday", [citation(0, "The launch is on Friday.")]),
            text_block(" and the budget is 40k.", [citation(1, "The budget is 40k."), citation(1, "40k")]),
        ]
    )

    result = answer_question("Launch and budget?", PASSAGES, client=client)

    assert result["answer"] == "The launch is Friday[1] and the budget is 40k.[2]"
    assert result["citations"] == [
        {"number": 1, "passage_id": "notes.md#1", "cited_text": "The launch is on Friday."},
        {"number": 2, "passage_id": "notes.md#2", "cited_text": "The budget is 40k."},
    ]


def test_skips_non_text_blocks():
    client = fake_client([SimpleNamespace(type="thinking", thinking="..."), text_block("Not in the documents.")])

    result = answer_question("Who won?", PASSAGES, client=client)

    assert result["answer"] == "Not in the documents."
    assert result["citations"] == []


def test_refusal_raises():
    client = fake_client([], stop_reason="refusal")

    with pytest.raises(RuntimeError):
        answer_question("anything", PASSAGES, client=client)
