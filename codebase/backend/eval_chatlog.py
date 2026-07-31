from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env

load_lab_env(ROOT)

from companion.answer import generate
from companion.retriever import load_corpus, search as corpus_search
from companion.classify import classify_turn
from providers import make_provider


CSV_PATH = ROOT.parent / "data" / "vlearn-pack" / "chatlog" / "chat_history_anonymized_for_hackathon.csv"


def parse_student_content(content: str) -> tuple[int | None, str, str]:
    """Parse student metadata prefix (Trang N, đoạn được chọn: "...") and extract actual query."""
    page: int | None = None
    selection: str = ""
    query: str = content.strip()

    prefix_match = re.match(r'^\(Trang\s+(\d+)(?:,\s*đoạn được chọn:\s*""(.*?)""|,\s*đoạn được chọn:\s*"(.*?)")?\)\s*(.*)$', content, re.DOTALL)
    if prefix_match:
        page = int(prefix_match.group(1))
        selection = (prefix_match.group(2) or prefix_match.group(3) or "").strip()
        query = (prefix_match.group(4) or "").strip()
    return page, selection, query


def load_chatlog_turns(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Chatlog dataset not found at {path}")

    turns_raw: dict[str, dict[str, Any]] = {}

    with path.open(mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            turn_id = row["turn_id"]
            if turn_id not in turns_raw:
                turns_raw[turn_id] = {
                    "turn_id": turn_id,
                    "conversation_id": row["conversation_id"],
                    "user_id": row["user_id"],
                    "day_code": row["day_code"],
                    "student": None,
                    "tutor": None,
                }
            if row["role"] == "student":
                page, sel, q = parse_student_content(row["content"])
                turns_raw[turn_id]["student"] = {
                    "raw_content": row["content"],
                    "page": page,
                    "selection": sel,
                    "query": q if q else row["content"],
                    "created_at": row["message_created_at"],
                }
            elif row["role"] == "tutor":
                turns_raw[turn_id]["tutor"] = {
                    "content": row["content"],
                    "citations": json.loads(row["citations"]) if row["citations"] else [],
                    "rating": row["rating"],
                    "latency_ms": int(row["avg_latency_ms"]) if row["avg_latency_ms"] else 0,
                }

    valid_turns = [t for t in turns_raw.values() if t["student"] is not None]
    return valid_turns


def run_evaluation(limit: int | None = None) -> dict[str, Any]:
    print(f"Loading chatlog dataset from: {CSV_PATH}")
    turns = load_chatlog_turns(CSV_PATH)
    if limit:
        turns = turns[:limit]
    print(f"Total valid turns loaded: {len(turns)}")

    corpus = load_corpus()
    print(f"Corpus chunks available: {len(corpus)}")

    # Provider setup
    provider_name = os.getenv("DEFAULT_PROVIDER", "nvidia")
    try:
        provider = make_provider(provider_name)
        print(f"Active LLM Provider: {provider.__class__.__name__}")
    except Exception as e:
        provider = None
        print(f"Warning: Provider setup failed ({e}), running in mock mode.")

    intent_counts: dict[str, int] = {}
    scope_counts: dict[str, int] = {}
    baseline_empty_citations = 0
    new_empty_citations = 0
    no_access_replies = 0
    refusals = 0
    handoffs_suggested = 0
    total_latency_ms = 0

    evaluated_cases: list[dict[str, Any]] = []

    start_time = time.time()

    for idx, turn in enumerate(turns, start=1):
        t_id = turn["turn_id"]
        st_data = turn["student"]
        tutor_data = turn["tutor"] or {}

        raw_query = st_data["query"]
        page = st_data["page"] or 1
        selection = st_data["selection"]

        # 1. Detect Intent & Scope
        # Phân tích hàng loạt 1.261 lượt: use_llm=False để không thả 1.261 lời gọi
        # classifier ra ngoài, nhưng vẫn đi qua cùng một điểm vào với pipeline.
        decision = classify_turn(
            raw_query,
            has_selection=bool(selection.strip()),
            current_day="day01",
            current_page=page,
            use_llm=False,
        )
        intent = decision.intent
        scope_res = decision.scope_result

        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        scope_counts[scope_res.scope] = scope_counts.get(scope_res.scope, 0) + 1

        # 2. Retrieval & Generation
        t0 = time.perf_counter()
        chunks = corpus_search(raw_query, scope_res, corpus, selection=selection)
        answer = generate(raw_query, scope_res, chunks, provider=provider)
        latency = int((time.perf_counter() - t0) * 1000)

        # Baseline metrics tracking
        orig_citations = tutor_data.get("citations", [])
        if not orig_citations:
            baseline_empty_citations += 1

        if not answer["sources"]:
            new_empty_citations += 1

        if scope_res.scope in ("out_of_scope", "ambiguous") or not chunks:
            handoffs_suggested += 1

        if "không tìm thấy" in (tutor_data.get("content") or "").lower():
            no_access_replies += 1

        total_latency_ms += latency

        case_record = {
            "turn_id": t_id,
            "student_query": raw_query[:100],
            "page": page,
            "intent": intent,
            "scope": scope_res.scope,
            "confidence": scope_res.confidence,
            "chunks_retrieved": len(chunks),
            "sources_cited": answer["sources"],
            "mode": answer["mode"],
            "latency_ms": latency,
            "baseline_citations": len(orig_citations),
        }
        evaluated_cases.append(case_record)

        if idx % 50 == 0 or idx == len(turns):
            print(f"Evaluated {idx}/{len(turns)} turns...")

    total_eval_time = time.time() - start_time
    avg_latency = total_latency_ms / len(turns) if turns else 0

    summary = {
        "dataset_path": str(CSV_PATH),
        "total_turns": len(turns),
        "total_eval_time_seconds": round(total_eval_time, 2),
        "avg_agent_latency_ms": round(avg_latency, 2),
        "intent_distribution": intent_counts,
        "scope_distribution": scope_counts,
        "metrics": {
            "baseline_empty_citation_rate": round(baseline_empty_citations / len(turns) * 100, 2),
            "smart_companion_empty_citation_rate": round(new_empty_citations / len(turns) * 100, 2),
            "handoff_or_clarification_suggested_rate": round(handoffs_suggested / len(turns) * 100, 2),
            "baseline_no_access_reply_count": no_access_replies,
        },
        "sample_evaluations": evaluated_cases[:10],
    }

    out_file = ROOT / "eval_results_chatlog.json"
    out_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nEvaluation complete! Results saved to {out_file}")

    return summary


if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_evaluation(limit=limit_val)
