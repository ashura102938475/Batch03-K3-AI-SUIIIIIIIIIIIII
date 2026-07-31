"""Choose when a learning question should use grounded external knowledge."""
from __future__ import annotations

from companion.text import fold_text, terms

MISSING_GROUNDING_SIGNALS = (
    "thieu du lieu",
    "khong du du lieu",
    "khong co thong tin",
    "khong de cap",
    "khong tim thay",
    "nguon khong du",
    "chua du can cu",
    "cannot answer from",
    "not enough information",
)


def should_try_external(query: str, scope_result, chunks, answer_text: str = "") -> bool:
    """Fallback only for implicit page scope, never for an explicitly requested slide."""
    if scope_result.scope == "external_knowledge":
        return True
    if scope_result.scope != "current_page" or scope_result.confidence == "cao":
        return False

    if answer_text and any(signal in fold_text(answer_text) for signal in MISSING_GROUNDING_SIGNALS):
        return True
    if not chunks:
        return True

    query_terms = terms(query)
    if not query_terms:
        return False
    source_terms = terms(" ".join(chunk.text for chunk in chunks))
    overlap = query_terms & source_terms
    return not overlap
