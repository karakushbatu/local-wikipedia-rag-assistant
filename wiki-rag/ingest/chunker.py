import re

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 100

# Patterns that indicate low-quality reference/bibliography sections
_JUNK_PATTERNS = [
    re.compile(r'^\s*==+\s*(References|Bibliography|Further reading|External links|Notes|Citations|See also|Footnotes)\s*==+', re.IGNORECASE | re.MULTILINE),
]

# A chunk is junk if it has high density of these markers
_JUNK_LINE_PATTERNS = [
    re.compile(r'doi:10\.\d{4}'),
    re.compile(r'Retrieved \d{1,2} \w+ \d{4}'),
    re.compile(r'ISBN \d'),
    re.compile(r'OCLC \d'),
    re.compile(r'Archived from'),
    re.compile(r'https?://web\.archive\.org'),
]


def _clean_text(text: str) -> str:
    """Strip excessive whitespace and normalize newlines."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    return text


def _strip_references_section(text: str) -> str:
    """Remove everything from the References/Bibliography heading onward."""
    for pattern in _JUNK_PATTERNS:
        match = pattern.search(text)
        if match:
            text = text[:match.start()]
    return text


def _is_low_quality(text: str) -> bool:
    """Return True if the chunk looks like a reference list or bibliography."""
    matches = sum(1 for p in _JUNK_LINE_PATTERNS if p.search(text))
    # If 2+ junk markers found in a 500-char chunk, it's low quality
    return matches >= 2


def chunk_text(
    text: str,
    entity_name: str,
    entity_type: str,
    source_url: str,
) -> list[dict]:
    """
    Sliding window chunker with overlap.
    Strips reference sections before chunking.
    Returns list of dicts: { "text": str, "metadata": dict }
    """
    text = _strip_references_section(text)
    text = _clean_text(text)

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text_slice = text[start:end]

        if len(chunk_text_slice) >= MIN_CHUNK_SIZE and not _is_low_quality(chunk_text_slice):
            chunks.append({
                "text": chunk_text_slice,
                "metadata": {
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "chunk_index": chunk_index,
                    "source_url": source_url,
                },
            })
            chunk_index += 1

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks
