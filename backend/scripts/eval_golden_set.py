from __future__ import annotations

import json
import math
import os
import re
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
from companion.retriever import Chunk, load_corpus, search as corpus_search
from companion.scope import detect_intent, detect_scope
from companion.text import fold_text
from providers import make_provider

GOLDEN_SET_PATH = ROOT / "eval" / "golden_set.json"
PAGE_CITATION_PATTERN = re.compile(r"^Trang (\d+)$")


def percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    position = (len(sorted_data) - 1) * p / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_data[lower]
    return sorted_data[lower] * (upper - position) + sorted_data[upper] * (position - lower)


def classify_behavior(scope: str, chunks: list[Chunk], answer: dict[str, Any]) -> str:
    if scope == "ambiguous":
        return "clarify"
    if scope == "out_of_scope":
        return "refuse"
    if not chunks or answer["mode"] == "guardrail":
        return "handoff"
    return "answer"


def content_matches(answer_text: str, expected: dict[str, Any]) -> bool:
    signals = expected.get("answer_must_contain_any", [])
    if not signals:
        return True
    folded_answer = fold_text(answer_text)
    return any(fold_text(signal) in folded_answer for signal in signals)


def citations_match(
    actual_sources: list[str],
    retrieved_sources: list[str],
    expected: dict[str, Any],
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    expected_behavior = expected["behavior"]
    minimum = int(expected.get("min_citations", 0))

    if expected_behavior != "answer":
        if actual_sources:
            failures.append(f"Expected no citations, got {actual_sources}")
        return not failures, failures

    if len(actual_sources) < minimum:
        failures.append(f"Expected at least {minimum} citations, got {len(actual_sources)}")

    unsupported = [source for source in actual_sources if source not in retrieved_sources]
    if unsupported:
        failures.append(f"Unsupported citations: {unsupported}")

    prefixes = expected.get("citation_prefixes", [])
    if prefixes:
        wrong_prefix = [source for source in actual_sources if not any(source.startswith(prefix) for prefix in prefixes)]
        if wrong_prefix:
            failures.append(f"Citations outside expected source types: {wrong_prefix}")

    allowed_range = expected.get("allowed_page_range")
    if allowed_range:
        start, end = allowed_range
        outside_range = []
        for source in actual_sources:
            match = PAGE_CITATION_PATTERN.match(source)
            if match and not start <= int(match.group(1)) <= end:
                outside_range.append(source)
        if outside_range:
            failures.append(f"Page citations outside {start}-{end}: {outside_range}")

    return not failures, failures


def generate_markdown_report(summary: dict[str, Any]) -> str:
    quality_bar = summary["quality_bar"]
    overall_passed = summary["overall_pass_percent"] >= quality_bar["overall_pass_percent"]
    safety_passed = summary["grounding_safety_failures"] == 0
    citation_passed = summary["citation_accuracy_percent"] >= 75
    live_p90_passed = summary["live_latency"]["p90_ms"] < 12000

    lines = [
        "# VLearn Smart Contextual Companion - End-to-End Evaluation",
        "",
        f"**Dataset:** `{summary['dataset_id']}`",
        f"**Cases:** `{summary['total_cases']}`",
        f"**Observed/chatlog-derived cases:** `{summary['observed_case_count']}`",
        f"**Provider/model:** `{summary['active_provider']}` / `{summary['active_model']}`",
        f"**Evaluation time:** `{summary['eval_timestamp']}`",
        "",
        "## Quality Bar",
        "",
        "| Metric | Result | Target | Status |",
        "|---|---:|---:|---|",
        f"| Overall case pass | {summary['passed_cases']}/{summary['total_cases']} ({summary['overall_pass_percent']}%) | >= {quality_bar['overall_pass_percent']}% | {'PASS' if overall_passed else 'FAIL'} |",
        f"| Citation accuracy on answer cases | {summary['citation_accuracy_percent']}% | >= 75% | {'PASS' if citation_passed else 'FAIL'} |",
        f"| Grounding safety failures | {summary['grounding_safety_failures']} | 0 | {'PASS' if safety_passed else 'FAIL'} |",
        f"| Live answer P90 latency | {summary['live_latency']['p90_ms']}ms | < 12000ms | {'PASS' if live_p90_passed else 'FAIL'} |",
        "",
        f"Critical rule: {quality_bar['critical_rule']}",
        "",
        "> Grounding safety checks unsupported citations and answering without retrieved evidence. "
        "Semantic hallucination still requires a human review of the saved answer text.",
        "",
        "## Capability Metrics",
        "",
        f"- Intent accuracy: **{summary['intent_accuracy_percent']}%**",
        f"- Scope accuracy: **{summary['scope_accuracy_percent']}%**",
        f"- Clarification accuracy: **{summary['clarification_accuracy_percent']}%**",
        f"- Behavior accuracy: **{summary['behavior_accuracy_percent']}%**",
        f"- Live/model cases: **{summary['mode_counts'].get('live', 0)}**",
        f"- Rule cases: **{summary['mode_counts'].get('rule', 0)}**",
        f"- Guardrail cases: **{summary['mode_counts'].get('guardrail', 0)}**",
        f"- Citation repairs: **{summary['citation_repairs']}**",
        f"- Mock/provider-error cases: **{summary['mode_counts'].get('mock', 0)}**",
        "",
        "## Detailed Results",
        "",
        "| ID | Expected behavior | Actual | Scope | Citations | Result | Latency |",
        "|---|---|---|---|---:|---|---:|",
    ]

    for detail in summary["case_details"]:
        citations = len(detail["sources_cited"])
        result = "PASS" if detail["case_pass"] else "FAIL"
        lines.append(
            f"| `{detail['id']}` | {detail['expected_behavior']} | {detail['actual_behavior']} | "
            f"{detail['actual_scope']} | {citations} | {result} | {detail['latency_ms']}ms |"
        )

    lines.extend(["", "## Failures", ""])
    failures = [detail for detail in summary["case_details"] if not detail["case_pass"]]
    if not failures:
        lines.append("No failed cases.")
    else:
        for detail in failures:
            lines.append(f"- `{detail['id']}`: {'; '.join(detail['failures'])}")
    return "\n".join(lines)


def run_golden_set_eval() -> dict[str, Any]:
    dataset = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    corpus = load_corpus()

    provider_name = os.getenv("DEFAULT_PROVIDER", "nvidia")
    try:
        provider = make_provider(provider_name)
    except Exception as exc:
        provider = None
        print(f"Provider setup failed: {exc}")

    counters = {
        "intent": 0,
        "scope": 0,
        "clarification": 0,
        "behavior": 0,
        "citation": 0,
        "content": 0,
        "case": 0,
    }
    category_breakdown: dict[str, dict[str, int]] = {}
    case_details: list[dict[str, Any]] = []
    all_latencies: list[float] = []
    live_latencies: list[float] = []
    mode_counts: dict[str, int] = {}
    grounding_safety_failures = 0
    guardrail_interventions = 0
    citation_repairs = 0
    answer_case_count = 0
    answer_citation_pass_count = 0

    print(f"Loaded {dataset['dataset_id']}: {len(cases)} cases, {len(corpus)} corpus chunks")

    for case in cases:
        expected = case["expect"]
        category = case["category"]
        category_breakdown.setdefault(category, {"total": 0, "passed": 0})
        category_breakdown[category]["total"] += 1

        started = time.perf_counter()
        intent = detect_intent(case["query"])
        scope_result = detect_scope(
            case["query"],
            has_selection=bool(case.get("selection", "").strip()),
            current_day=case["current_day"],
            current_page=case["current_page"],
        )
        chunks = corpus_search(
            case["query"],
            scope_result,
            corpus,
            selection=case.get("selection", ""),
        )
        answer = generate(
            case["query"],
            scope_result,
            chunks,
            provider=provider,
            include_external_citations=False,
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        all_latencies.append(latency_ms)
        mode_counts[answer["mode"]] = mode_counts.get(answer["mode"], 0) + 1
        guardrail_interventions += int(answer["mode"] == "guardrail")
        citation_repairs += int(answer.get("citation_repaired", False))
        if answer["mode"] == "live":
            live_latencies.append(latency_ms)

        actual_behavior = classify_behavior(scope_result.scope, chunks, answer)
        intent_pass = intent == expected["intent"]
        scope_pass = scope_result.scope == expected["scope"]
        clarification_pass = scope_result.needs_clarification == expected["needs_clarification"]
        behavior_pass = actual_behavior == expected["behavior"]
        citation_pass, citation_failures = citations_match(
            answer["sources"],
            answer["retrieved_sources"],
            expected,
        )
        content_pass = content_matches(answer["text"], expected)
        live_mode_pass = expected["behavior"] != "answer" or answer["mode"] == "live"

        safety_failures: list[str] = []
        if answer["sources"] and any(source not in answer["retrieved_sources"] for source in answer["sources"]):
            safety_failures.append("source_not_retrieved")
        if expected["behavior"] in ("handoff", "refuse", "clarify") and actual_behavior == "answer":
            safety_failures.append("answered_without_permission_or_evidence")
        grounding_safe = not safety_failures
        if not grounding_safe:
            grounding_safety_failures += 1

        failures: list[str] = []
        if not intent_pass:
            failures.append(f"intent expected {expected['intent']}, got {intent}")
        if not scope_pass:
            failures.append(f"scope expected {expected['scope']}, got {scope_result.scope}")
        if not clarification_pass:
            failures.append("clarification behavior mismatch")
        if not behavior_pass:
            failures.append(f"behavior expected {expected['behavior']}, got {actual_behavior}")
        failures.extend(citation_failures)
        if not content_pass:
            failures.append("answer misses all required content signals")
        if not live_mode_pass:
            failures.append(f"answer case did not use live model (mode={answer['mode']})")
        if not grounding_safe:
            failures.append(f"grounding safety failure: {safety_failures}")

        case_pass = not failures
        checks = {
            "intent": intent_pass,
            "scope": scope_pass,
            "clarification": clarification_pass,
            "behavior": behavior_pass,
            "citation": citation_pass,
            "content": content_pass,
            "case": case_pass,
        }
        for key, passed in checks.items():
            counters[key] += int(passed)

        if expected["behavior"] == "answer":
            answer_case_count += 1
            answer_citation_pass_count += int(citation_pass)

        if case_pass:
            category_breakdown[category]["passed"] += 1

        case_details.append({
            "id": case["id"],
            "category": category,
            "origin": case.get("origin", ""),
            "turn_id": case.get("turn_id"),
            "query": case["query"],
            "expected_intent": expected["intent"],
            "actual_intent": intent,
            "intent_pass": intent_pass,
            "expected_scope": expected["scope"],
            "actual_scope": scope_result.scope,
            "scope_pass": scope_pass,
            "expected_clarification": expected["needs_clarification"],
            "actual_clarification": scope_result.needs_clarification,
            "clarification_pass": clarification_pass,
            "expected_behavior": expected["behavior"],
            "actual_behavior": actual_behavior,
            "behavior_pass": behavior_pass,
            "citation_pass": citation_pass,
            "content_pass": content_pass,
            "grounding_safe": grounding_safe,
            "retrieved_sources": answer["retrieved_sources"],
            "sources_cited": answer["sources"],
            "invalid_citations": answer.get("invalid_citations", []),
            "citation_repaired": answer.get("citation_repaired", False),
            "mode": answer["mode"],
            "model": answer["model"],
            "answer": answer["text"],
            "error": answer["error"],
            "case_pass": case_pass,
            "failures": failures,
            "latency_ms": latency_ms,
        })
        print(f"{case['id']}: {'PASS' if case_pass else 'FAIL'} ({answer['mode']}, {latency_ms}ms)")

    total = len(cases)
    observed_count = sum(1 for case in cases if case.get("origin", "").startswith("chatlog"))
    active_model = getattr(provider, "default_model", None) if provider else None
    summary = {
        "dataset_id": dataset["dataset_id"],
        "total_cases": total,
        "observed_case_count": observed_count,
        "eval_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_provider": provider.__class__.__name__ if provider else "MOCK",
        "active_model": active_model,
        "quality_bar": dataset["quality_bar"],
        "passed_cases": counters["case"],
        "overall_pass_percent": round(counters["case"] / total * 100, 2),
        "intent_accuracy_percent": round(counters["intent"] / total * 100, 2),
        "scope_accuracy_percent": round(counters["scope"] / total * 100, 2),
        "clarification_accuracy_percent": round(counters["clarification"] / total * 100, 2),
        "behavior_accuracy_percent": round(counters["behavior"] / total * 100, 2),
        "citation_accuracy_percent": round(answer_citation_pass_count / answer_case_count * 100, 2),
        "grounding_safety_failures": grounding_safety_failures,
        "guardrail_interventions": guardrail_interventions,
        "citation_repairs": citation_repairs,
        "mode_counts": mode_counts,
        "latency": {
            "avg_ms": round(sum(all_latencies) / total, 2),
            "p50_ms": round(percentile(all_latencies, 50), 2),
            "p90_ms": round(percentile(all_latencies, 90), 2),
        },
        "live_latency": {
            "count": len(live_latencies),
            "avg_ms": round(sum(live_latencies) / len(live_latencies), 2) if live_latencies else 0,
            "p50_ms": round(percentile(live_latencies, 50), 2),
            "p90_ms": round(percentile(live_latencies, 90), 2),
        },
        "category_breakdown": category_breakdown,
        "case_details": case_details,
    }

    json_out = ROOT / "eval" / "eval_golden_set_results.json"
    json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_out = ROOT / "eval" / "EVAL_REPORT.md"
    report_out.write_text(generate_markdown_report(summary), encoding="utf-8")

    print(
        f"Completed: {summary['passed_cases']}/{total} passed, "
        f"citation accuracy {summary['citation_accuracy_percent']}%, "
        f"grounding safety failures {grounding_safety_failures}"
    )
    return summary


if __name__ == "__main__":
    run_golden_set_eval()
