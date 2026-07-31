"""Ghi trace mỗi lượt hỏi-đáp ra runs/.

Rubric R5 đòi "≥1 lời gọi AI thật ở quyết định trung tâm (log/trace trong repo)".
File này chính là bằng chứng đó — và cũng là input để dựng golden set ở CP3.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"


def write_turn_trace(record: dict[str, Any]) -> Path:
    RUNS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    path = RUNS_DIR / f"turn_{stamp}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def build_record(*, query, intent, scope_result, chunks, answer, selection="") -> dict[str, Any]:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "question": query,
        "has_selection": bool(selection.strip()),
        "intent": intent,
        "scope": scope_result.scope,
        "scope_label": scope_result.label,
        "confidence": scope_result.confidence,
        "reason": scope_result.reason,
        "target_day": scope_result.target_day,
        "target_page": scope_result.target_page,
        "page_range": list(scope_result.page_range) if scope_result.page_range else None,
        "retrieved_chunk_ids": [c.chunk_id for c in chunks],
        "sources": answer["sources"],
        "external_sources": answer.get("external_sources", []),
        "untrusted_found": answer["untrusted_found"],
        "mode": answer["mode"],
        "model": answer["model"],
        "latency_ms": answer["latency_ms"],
        "error": answer["error"],
        "response_text": answer["text"],
    }
