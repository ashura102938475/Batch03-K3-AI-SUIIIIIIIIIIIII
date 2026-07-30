from __future__ import annotations

from typing import Any

from companion.retriever import load_corpus, search as corpus_search
from companion.scope import detect_intent, detect_scope
from companion.answer import generate


CORPUS = load_corpus()


def detect_scope_tool(query: str, current_day: str = "day01", current_page: int = 1, selection: str = "") -> dict[str, Any]:
    """Detect student intent and query scope."""
    intent = detect_intent(query)
    scope_res = detect_scope(
        query=query,
        has_selection=bool(selection.strip()),
        current_day=current_day,
        current_page=current_page,
    )
    return {
        "intent": intent,
        "scope": scope_res.scope,
        "label": scope_res.label,
        "confidence": scope_res.confidence,
        "reason": scope_res.reason,
        "needs_clarification": scope_res.needs_clarification,
    }


def search_corpus_tool(query: str, scope: str = "current_page", current_day: str = "day01", current_page: int = 1, selection: str = "") -> dict[str, Any]:
    """Search slide PDF and transcript corpus pre-filtered by scope."""
    scope_res = detect_scope(query, has_selection=bool(selection.strip()), current_day=current_day, current_page=current_page)
    scope_res.scope = scope
    chunks = corpus_search(query, scope_res, CORPUS, selection=selection)
    return {
        "count": len(chunks),
        "chunks": [
            {
                "doc_id": c.doc_id,
                "page": c.page,
                "cite": c.cite,
                "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
            }
            for c in chunks
        ],
    }


def escalate_ta_tool(reason: str, student_query: str) -> dict[str, Any]:
    """Escalate unresolved query or low-confidence response to TA."""
    return {
        "status": "escalated",
        "reason": reason,
        "query": student_query,
        "message": "Đã ghi nhận yêu cầu chuyển TA.",
    }
