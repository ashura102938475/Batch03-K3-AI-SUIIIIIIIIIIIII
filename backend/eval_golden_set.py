from __future__ import annotations

import json
import os
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
from companion.scope import detect_intent, detect_scope
from providers import make_provider

GOLDEN_SET_PATH = ROOT / "eval" / "golden_set.json"


def _count_numbered_items(text: str) -> int:
    import re
    return len(re.findall(r"(?m)^\s*\d+[\.)]\s+", text))


def _answer_expectation_pass(answer_text: str, sources: list[str], expect: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    folded_answer = answer_text.lower()

    for forbidden in expect.get("forbidden_text", []):
        if forbidden.lower() in folded_answer:
            failures.append(f"forbidden_text:{forbidden}")

    for required in expect.get("required_text", []):
        if required.lower() not in folded_answer:
            failures.append(f"required_text:{required}")

    for source in expect.get("source_includes", []):
        if not any(source in cite for cite in sources):
            failures.append(f"source_includes:{source}")

    if "exact_sources" in expect and sources != expect["exact_sources"]:
        failures.append(f"exact_sources:{expect['exact_sources']},actual:{sources}")

    exact_count = expect.get("exact_numbered_items")
    if exact_count is not None:
        actual_count = _count_numbered_items(answer_text)
        if actual_count != exact_count:
            failures.append(f"exact_numbered_items:{exact_count},actual:{actual_count}")

    if expect.get("requires_table") and "|" not in answer_text:
        failures.append("requires_table")

    return not failures, failures


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
    answer_correct = 0
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
            results_by_category[cat] = {"total": 0, "intent_correct": 0, "scope_correct": 0, "clarification_correct": 0, "answer_correct": 0}

        results_by_category[cat]["total"] += 1

        # 1. Detect Intent & Scope
        t0 = time.perf_counter()
        intent = detect_intent(query)
        scope_res = detect_scope(query, has_selection=bool(selection.strip()), current_day=day, current_page=page)

        # 2. Retrieve & Generate
        chunks = corpus_search(query, scope_res, corpus, selection=selection, task=intent)
        answer = generate(query, scope_res, chunks, provider=provider, task=intent)
        latency = int((time.perf_counter() - t0) * 1000)
        total_latency_ms += latency

        # Checks
        is_intent_pass = intent == expect["intent"]
        expected_target_page = expect.get("target_page")
        expected_page_range = tuple(expect["page_range"]) if "page_range" in expect else None
        is_target_page_pass = expected_target_page is None or scope_res.target_page == expected_target_page
        is_page_range_pass = expected_page_range is None or scope_res.page_range == expected_page_range
        is_scope_pass = scope_res.scope == expect["scope"] and is_target_page_pass and is_page_range_pass
        is_clarify_pass = scope_res.needs_clarification == expect["needs_clarification"]
        is_answer_pass, answer_failures = _answer_expectation_pass(answer["text"], answer["sources"], expect)

        if is_intent_pass:
            intent_correct += 1
            results_by_category[cat]["intent_correct"] += 1
        if is_scope_pass:
            scope_correct += 1
            results_by_category[cat]["scope_correct"] += 1
        if is_clarify_pass:
            clarification_correct += 1
            results_by_category[cat]["clarification_correct"] += 1
        if is_answer_pass:
            answer_correct += 1
            results_by_category[cat]["answer_correct"] += 1

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
            "expected_target_page": expected_target_page,
            "actual_target_page": scope_res.target_page,
            "target_page_pass": is_target_page_pass,
            "expected_page_range": list(expected_page_range) if expected_page_range else None,
            "actual_page_range": list(scope_res.page_range) if scope_res.page_range else None,
            "page_range_pass": is_page_range_pass,
            "scope_pass": is_scope_pass,
            "expected_clarification": expect["needs_clarification"],
            "actual_clarification": scope_res.needs_clarification,
            "sources_cited": answer["sources"],
            "answer_pass": is_answer_pass,
            "answer_failures": answer_failures,
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
        "answer_quality_percent": round(answer_correct / total_cases * 100, 2),
        "citation_presence_rate_percent": round(cited_count / total_cases * 100, 2),
        "avg_latency_ms": round(total_latency_ms / total_cases, 2),
        "category_breakdown": results_by_category,
        "case_details": case_details,
    }

    out_file = ROOT / "eval" / "eval_golden_set_results.json"
    out_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGolden Set Evaluation Complete! Results saved to {out_file}")

    print("\n--- SUMMARY METRICS ---")
    print(f"Scope Detection Accuracy       : {summary['scope_accuracy_percent']}%")
    print(f"Intent Classification Accuracy  : {summary['intent_accuracy_percent']}%")
    print(f"Clarification Accuracy          : {summary['clarification_accuracy_percent']}%")
    print(f"Answer Quality Checks           : {summary['answer_quality_percent']}%")
    print(f"Citation Presence Rate          : {summary['citation_presence_rate_percent']}%")
    print(f"Average Latency                 : {summary['avg_latency_ms']}ms")

    return summary


if __name__ == "__main__":
    run_golden_set_eval()
