"""Splits long text into overlapping passages of a bounded word count.

Exists so every text format produces passages small enough to rank well. Must
not know about file formats, passage ids or where the text came from.
"""

CHUNK_WORDS = 200
# Overlap means a sentence cut at a window boundary still appears whole in one passage.
CHUNK_OVERLAP_WORDS = 40


def chunk_text(text: str, max_words: int = CHUNK_WORDS, overlap_words: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max_words - overlap_words
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start : start + max_words]))
        if start + max_words >= len(words):
            break
    return chunks
