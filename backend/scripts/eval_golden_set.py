from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env

load_lab_env(ROOT)

from companion.answer import generate
from companion.retriever import load_corpus, search as corpus_search
from companion.scope import detect_intent, detect_scope
from providers import make_provider

GOLDEN_SET_PATH = ROOT / "eval" / "golden_set.json"


def run_golden_set_eval() -> dict[str, Any]:
    if not GOLDEN_SET_PATH.exists():
        raise FileNotFoundError(f"Golden Set file not found at {GOLDEN_SET_PATH}")

    dataset = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    print(f"Loaded Golden Set dataset: {dataset['dataset_id']} ({len(cases)} cases across 6 categories)")

    corpus = load_corpus()
    print(f"Corpus chunks loaded: {len(corpus)}")

    provider_name = os.getenv("DEFAULT_PROVIDER", "nvidia")
    try:
        provider = make_provider(provider_name)
        print(f"Active LLM Provider: {provider.__class__.__name__}")
    except Exception as exc:
        provider = None
        print(f"Warning: Provider setup failed ({exc}), running in mock mode.")

    intent_correct = 0
    scope_correct = 0
    clarification_correct = 0
    cited_count = 0
    total_latency_ms = 0

    results_by_category: dict[str, dict[str, int]] = {}
    case_details: list[dict[str, Any]] = []

    for case in cases:
        c_id = case["id"]
        cat = case["category"]
        query = case["query"]
        day = case["current_day"]
        page = case["current_page"]
        selection = case.get("selection", "")
        expect = case["expect"]

        if cat not in results_by_category:
            results_by_category[cat] = {"total": 0, "intent_correct": 0, "scope_correct": 0, "clarification_correct": 0}

        results_by_category[cat]["total"] += 1

        t0 = time.perf_counter()
        intent = detect_intent(query)
        scope_res = detect_scope(query, has_selection=bool(selection.strip()), current_day=day, current_page=page)

        chunks = corpus_search(query, scope_res, corpus, selection=selection)
        answer = generate(query, scope_res, chunks, provider=provider)
        latency = int((time.perf_counter() - t0) * 1000)
        total_latency_ms += latency

        is_intent_pass = intent == expect["intent"]
        is_scope_pass = scope_res.scope == expect["scope"]
        is_clarify_pass = scope_res.needs_clarification == expect["needs_clarification"]

        if is_intent_pass:
            intent_correct += 1
            results_by_category[cat]["intent_correct"] += 1
        if is_scope_pass:
            scope_correct += 1
            results_by_category[cat]["scope_correct"] += 1
        if is_clarify_pass:
            clarification_correct += 1
            results_by_category[cat]["clarification_correct"] += 1

        if answer["sources"]:
            cited_count += 1

        case_details.append({
            "id": c_id,
            "category": cat,
            "query": query,
            "expected_intent": expect["intent"],
            "actual_intent": intent,
            "intent_pass": is_intent_pass,
            "expected_scope": expect["scope"],
            "actual_scope": scope_res.scope,
            "scope_pass": is_scope_pass,
            "expected_clarification": expect["needs_clarification"],
            "actual_clarification": scope_res.needs_clarification,
            "sources_cited": answer["sources"],
            "mode": answer["mode"],
            "latency_ms": latency,
        })

    total_cases = len(cases)
    summary = {
        "dataset_id": dataset["dataset_id"],
        "total_cases": total_cases,
        "active_provider": provider.__class__.__name__ if provider else "MOCK",
        "intent_accuracy_percent": round(intent_correct / total_cases * 100, 2),
        "scope_accuracy_percent": round(scope_correct / total_cases * 100, 2),
        "clarification_accuracy_percent": round(clarification_correct / total_cases * 100, 2),
        "citation_presence_rate_percent": round(cited_count / total_cases * 100, 2),
        "avg_latency_ms": round(total_latency_ms / total_cases, 2),
        "category_breakdown": results_by_category,
        "case_details": case_details,
    }

    out_file = ROOT / "eval" / "eval_golden_set_results.json"
    out_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGolden Set Evaluation Complete! Results saved to {out_file}")
    return summary


if __name__ == "__main__":
    run_golden_set_eval()
