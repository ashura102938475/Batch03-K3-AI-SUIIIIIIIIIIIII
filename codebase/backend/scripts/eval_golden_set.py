from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent.parent
EVAL_DIR = REPO_ROOT / "eval"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env

load_lab_env(ROOT)

from companion.answer import _validate_citations, generate
from companion.retriever import Chunk, load_corpus, search as corpus_search
from companion.scope import detect_intent, detect_scope
from companion.text import fold_text
from providers import make_provider

PAGE_CITATION_PATTERN = re.compile(r"^Trang (\d+)$")
EVALUATOR_VERSION = "3.0"


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


def classify_behavior(scope: str, sources: list[str], mode: str, ta_handoff_suggested: bool) -> str:
    if scope == "ambiguous":
        return "clarify"
    if scope == "out_of_scope":
        return "refuse"
    if not sources and (ta_handoff_suggested or mode == "guardrail"):
        return "handoff"
    return "answer"


def _contains_any(text: str, signals: list[str]) -> bool:
    folded = fold_text(text)
    return any(fold_text(signal) in folded for signal in signals)


def _contains_all(text: str, signals: list[str]) -> bool:
    folded = fold_text(text)
    return all(fold_text(signal) in folded for signal in signals)


def _answer_blocks(answer_text: str) -> list[str]:
    lines = [line.strip() for line in answer_text.splitlines() if line.strip()]
    parts = [
        part.strip()
        for line in lines
        for part in re.split(r"(?<=[.!?])\s+", line)
        if part.strip()
    ]
    merged: list[str] = []
    for part in parts:
        if merged and re.fullmatch(r"(?:\[[^\[\]]+\]\s*)+", part):
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return merged


def evaluate_content(
    answer_text: str,
    expected: dict[str, Any],
    corpus: list[Chunk],
) -> tuple[bool, bool, dict[str, Any], list[str]]:
    failures: list[str] = []

    legacy_any = expected.get("answer_must_contain_any", [])
    if legacy_any and not _contains_any(answer_text, legacy_any):
        failures.append("answer misses all legacy content signals")

    required_all = expected.get("answer_must_contain_all", [])
    missing_required = [signal for signal in required_all if not _contains_any(answer_text, [signal])]
    if missing_required:
        failures.append(f"answer misses required signals: {missing_required}")

    forbidden = expected.get("forbidden_signals", [])
    found_forbidden = [signal for signal in forbidden if _contains_any(answer_text, [signal])]
    if found_forbidden:
        failures.append(f"answer contains forbidden signals: {found_forbidden}")

    claims = expected.get("claims", [])
    minimum = int(expected.get("min_claims", len(claims)))
    matched_ids: list[str] = []
    grounded_ids: list[str] = []
    blocks = _answer_blocks(answer_text)
    answer_sources = set(_validate_citations(answer_text, corpus)[0])

    minimum_numbered_items = int(expected.get("min_numbered_items", 0))
    numbered_items = {
        int(number)
        for number in re.findall(r"(?m)^\s*(?:câu\s*)?(\d+)[.)]", fold_text(answer_text))
    }
    if len(numbered_items) < minimum_numbered_items:
        failures.append(
            f"expected at least {minimum_numbered_items} numbered items, got {len(numbered_items)}"
        )

    for claim in claims:
        signals = claim.get("signals_any", [])
        matching_blocks = [block for block in blocks if _contains_any(block, signals)]
        if not matching_blocks:
            continue
        matched_ids.append(claim["id"])

        allowed_sources = set(claim.get("sources_any", []))
        if not allowed_sources:
            grounded_ids.append(claim["id"])
            continue
        for block in matching_blocks:
            valid_sources, _ = _validate_citations(block, corpus)
            if allowed_sources.intersection(valid_sources):
                grounded_ids.append(claim["id"])
                break
        else:
            if len(answer_sources) == 1 and allowed_sources.intersection(answer_sources):
                grounded_ids.append(claim["id"])

    claim_coverage_pass = len(matched_ids) >= minimum
    claim_grounding_pass = len(grounded_ids) >= minimum
    if claims and not claim_coverage_pass:
        failures.append(f"matched {len(matched_ids)}/{minimum} required claims")
    if claims and not claim_grounding_pass:
        failures.append(f"grounded {len(grounded_ids)}/{minimum} required claims at claim level")

    content_pass = not failures
    details = {
        "required_claims": minimum,
        "matched_claims": matched_ids,
        "grounded_claims": grounded_ids,
        "missing_required_signals": missing_required,
        "found_forbidden_signals": found_forbidden,
        "numbered_items": sorted(numbered_items),
    }
    return content_pass, claim_grounding_pass, details, failures


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
            failures.append(f"expected no citations, got {actual_sources}")
        return not failures, failures

    if len(actual_sources) < minimum:
        failures.append(f"expected at least {minimum} citations, got {len(actual_sources)}")

    unsupported = [source for source in actual_sources if source not in retrieved_sources]
    if unsupported:
        failures.append(f"citations were not retrieved: {unsupported}")

    allowed_range = expected.get("allowed_page_range")
    if allowed_range:
        start, end = allowed_range
        outside_range = []
        for source in actual_sources:
            match = PAGE_CITATION_PATTERN.match(source)
            if match and not start <= int(match.group(1)) <= end:
                outside_range.append(source)
        if outside_range:
            failures.append(f"page citations outside {start}-{end}: {outside_range}")

    return not failures, failures


def _run_direct(case: dict[str, Any], corpus: list[Chunk], provider: Any) -> dict[str, Any]:
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
    ta_handoff = bool(
        scope_result.scope in ("out_of_scope", "ambiguous")
        or not chunks
        or answer["mode"] in ("mock", "guardrail")
        or (chunks and not answer["sources"])
    )
    return {
        "http_status": None,
        "intent": intent,
        "scope": scope_result.scope,
        "needs_clarification": scope_result.needs_clarification,
        "sources": answer["sources"],
        "retrieved_sources": answer["retrieved_sources"],
        "answer": answer["text"],
        "mode": answer["mode"],
        "model": answer["model"],
        "error": answer["error"],
        "ta_handoff_suggested": ta_handoff,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def _api_runner(corpus: list[Chunk]):
    from fastapi.testclient import TestClient

    from api import app

    client = TestClient(app)
    chunk_citations = {chunk.chunk_id: chunk.cite for chunk in corpus}

    def run(case: dict[str, Any], provider_name: str | None) -> dict[str, Any]:
        payload = {
            "query": case["query"],
            "current_day": case["current_day"],
            "current_page": case["current_page"],
            "selection": case.get("selection", ""),
            "forced_scope": case.get("forced_scope"),
            "provider": provider_name,
        }
        started = time.perf_counter()
        response = client.post("/api/v1/companion/chat", json=payload)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        if response.status_code != 200:
            return {
                "http_status": response.status_code,
                "intent": "api_error",
                "scope": "api_error",
                "needs_clarification": False,
                "sources": [],
                "retrieved_sources": [],
                "answer": response.text,
                "mode": "api_error",
                "model": None,
                "error": response.text,
                "ta_handoff_suggested": False,
                "latency_ms": latency_ms,
            }

        data = response.json()
        trace_path = ROOT / "runs" / data["trace_file"]
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        selection_source = f"Trang {case['current_page']}"
        retrieved_sources = [
            selection_source if chunk_id == "selection" else chunk_citations[chunk_id]
            for chunk_id in trace.get("retrieved_chunk_ids", [])
            if chunk_id == "selection" or chunk_id in chunk_citations
        ]
        return {
            "http_status": response.status_code,
            "intent": data["intent"],
            "scope": data["scope"],
            "needs_clarification": data["needs_clarification"],
            "sources": data["sources_used"],
            "retrieved_sources": list(dict.fromkeys(retrieved_sources)),
            "answer": data["answer"],
            "mode": data["mode"],
            "model": data["model"],
            "error": trace.get("error"),
            "ta_handoff_suggested": data["ta_handoff_suggested"],
            "latency_ms": latency_ms,
        }

    return client, run


def _format_rate(passed: int, total: int) -> float:
    return round(passed / total * 100, 2) if total else 0.0


def generate_markdown_report(summary: dict[str, Any]) -> str:
    quality_bar = summary["quality_bar"]
    checks = summary["quality_checks"]
    lines = [
        f"# VLearn Smart Contextual Companion - Evaluation {summary['version']}",
        "",
        f"**Dataset:** `{summary['dataset_id']}`",
        f"**Dataset SHA-256:** `{summary['dataset_sha256']}`",
        f"**Evaluator:** `{summary['evaluator_version']}`",
        f"**Transport:** `{summary['transport']}`",
        f"**Cases:** `{summary['total_cases']}`",
        f"**Observed cases:** `{summary['observed_case_count']}`",
        f"**Verbatim/field-observation cases:** `{summary['verbatim_case_count']}`",
        f"**Provider/model:** `{summary['active_provider']}` / `{summary['active_model']}`",
        f"**Evaluation time:** `{summary['eval_timestamp']}`",
        "",
        "## Quality Gates",
        "",
        "| Metric | Result | Target | Status |",
        "|---|---:|---:|---|",
        f"| Overall case pass | {summary['passed_cases']}/{summary['total_cases']} ({summary['overall_pass_percent']}%) | >= {quality_bar['overall_pass_percent']}% | {'PASS' if checks['overall'] else 'FAIL'} |",
        f"| Decision pass | {summary['decision_pass_percent']}% | >= {quality_bar['decision_pass_percent']}% | {'PASS' if checks['decision'] else 'FAIL'} |",
        f"| Live answer pass | {summary['live_answer_pass_percent']}% | >= {quality_bar['live_answer_pass_percent']}% | {'PASS' if checks['live_answer'] else 'FAIL'} |",
        f"| Citation grounding | {summary['citation_grounding_percent']}% | >= {quality_bar['citation_grounding_percent']}% | {'PASS' if checks['citation_grounding'] else 'FAIL'} |",
        f"| Critical failures | {summary['critical_failure_count']} | <= {quality_bar['max_critical_failures']} | {'PASS' if checks['critical'] else 'FAIL'} |",
        f"| Live answer P90 latency | {summary['live_latency']['p90_ms']}ms | < 12000ms | {'PASS' if checks['latency'] else 'FAIL'} |",
        "",
        f"Critical rule: {quality_bar['critical_rule']}",
        "",
        "> Claim-level grounding requires a human-labelled expected claim to appear near an allowed citation. "
        "It is stricter than source membership, but final semantic review is still required.",
        "",
        "## Capability Metrics",
        "",
        f"- Intent accuracy: **{summary['intent_accuracy_percent']}%**",
        f"- Scope accuracy: **{summary['scope_accuracy_percent']}%**",
        f"- Clarification accuracy: **{summary['clarification_accuracy_percent']}%**",
        f"- Behavior accuracy: **{summary['behavior_accuracy_percent']}%**",
        f"- TA handoff accuracy: **{summary['ta_handoff_accuracy_percent']}%**",
        f"- Claim coverage: **{summary['claim_coverage_percent']}%**",
        f"- Live/model cases: **{summary['mode_counts'].get('live', 0)}**",
        f"- Rule cases: **{summary['mode_counts'].get('rule', 0)}**",
        f"- Mock/provider-error cases: **{summary['mode_counts'].get('mock', 0) + summary['mode_counts'].get('api_error', 0)}**",
        "",
        "## Detailed Results",
        "",
        "| ID | Expected | Actual | Scope | Claims | Citations | Result | Latency |",
        "|---|---|---|---|---:|---:|---|---:|",
    ]

    for detail in summary["case_details"]:
        result = "PASS" if detail["case_pass"] else "FAIL"
        claim_count = len(detail["claim_details"]["grounded_claims"])
        lines.append(
            f"| `{detail['id']}` | {detail['expected_behavior']} | {detail['actual_behavior']} | "
            f"{detail['actual_scope']} | {claim_count} | {len(detail['sources_cited'])} | "
            f"{result} | {detail['latency_ms']}ms |"
        )

    lines.extend(["", "## Failures", ""])
    failures = [detail for detail in summary["case_details"] if not detail["case_pass"]]
    if not failures:
        lines.append("No failed cases.")
    else:
        for detail in failures:
            critical = " **CRITICAL**" if detail["critical"] else ""
            lines.append(f"- `{detail['id']}`{critical}: {'; '.join(detail['failures'])}")
    return "\n".join(lines) + "\n"


def run_golden_set_eval(
    *,
    version: str = "v3",
    dataset_path: str | Path | None = None,
    transport: str = "api",
    provider_name: str | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    path = Path(dataset_path) if dataset_path else EVAL_DIR / f"golden_set_{version}.json"
    dataset_bytes = path.read_bytes()
    dataset = json.loads(dataset_bytes.decode("utf-8"))
    cases = dataset["cases"]
    corpus = load_corpus()
    provider_name = provider_name or os.getenv("DEFAULT_PROVIDER", "nvidia")

    provider = None
    api_client = None
    if transport == "api":
        api_client, run_case = _api_runner(corpus)
        health = api_client.get("/health").json()
        active_provider = health["active_provider"]
        active_model = health["default_model"]
    elif transport == "direct":
        try:
            provider = make_provider(provider_name)
        except Exception as exc:
            print(f"Provider setup failed: {exc}")
        run_case = lambda case, _: _run_direct(case, corpus, provider)
        active_provider = provider.__class__.__name__ if provider else "MOCK"
        active_model = getattr(provider, "default_model", None) if provider else None
    else:
        raise ValueError(f"Unsupported transport: {transport}")

    counters = {
        "intent": 0,
        "scope": 0,
        "clarification": 0,
        "behavior": 0,
        "ta_handoff": 0,
        "decision": 0,
        "citation": 0,
        "content": 0,
        "claim_grounding": 0,
        "case": 0,
    }
    case_details: list[dict[str, Any]] = []
    category_breakdown: dict[str, dict[str, int]] = {}
    mode_counts: dict[str, int] = {}
    all_latencies: list[float] = []
    live_latencies: list[float] = []
    answer_case_count = 0
    live_answer_passed = 0
    claim_case_count = 0
    claim_case_passed = 0
    critical_failure_ids: list[str] = []

    print(
        f"Loaded {dataset['dataset_id']}: {len(cases)} cases, "
        f"{len(corpus)} chunks, transport={transport}"
    )

    for case in cases:
        expected = case["expect"]
        result = run_case(case, provider_name)
        all_latencies.append(result["latency_ms"])
        mode_counts[result["mode"]] = mode_counts.get(result["mode"], 0) + 1
        if result["mode"] == "live":
            live_latencies.append(result["latency_ms"])

        actual_behavior = classify_behavior(
            result["scope"],
            result["sources"],
            result["mode"],
            result["ta_handoff_suggested"],
        )
        intent_pass = result["intent"] == expected["intent"]
        scope_pass = result["scope"] == expected["scope"]
        clarification_pass = result["needs_clarification"] == expected["needs_clarification"]
        behavior_pass = actual_behavior == expected["behavior"]
        ta_expected = expected.get("ta_handoff_suggested")
        ta_pass = ta_expected is None or result["ta_handoff_suggested"] == ta_expected
        decision_pass = all((intent_pass, scope_pass, clarification_pass, behavior_pass, ta_pass))

        citation_pass, citation_failures = citations_match(
            result["sources"],
            result["retrieved_sources"],
            expected,
        )
        content_pass, claim_grounding_pass, claim_details, content_failures = evaluate_content(
            result["answer"],
            expected,
            corpus,
        )
        live_mode_pass = expected["behavior"] != "answer" or result["mode"] == "live"

        grounding_failures: list[str] = []
        if any(source not in result["retrieved_sources"] for source in result["sources"]):
            grounding_failures.append("source_not_retrieved")
        if expected["behavior"] != "answer" and result["sources"]:
            grounding_failures.append("cited_answer_when_answer_not_allowed")
        grounding_safe = not grounding_failures

        failures: list[str] = []
        if not intent_pass:
            failures.append(f"intent expected {expected['intent']}, got {result['intent']}")
        if not scope_pass:
            failures.append(f"scope expected {expected['scope']}, got {result['scope']}")
        if not clarification_pass:
            failures.append("clarification behavior mismatch")
        if not behavior_pass:
            failures.append(f"behavior expected {expected['behavior']}, got {actual_behavior}")
        if not ta_pass:
            failures.append(
                f"TA handoff expected {ta_expected}, got {result['ta_handoff_suggested']}"
            )
        failures.extend(citation_failures)
        failures.extend(content_failures)
        if not live_mode_pass:
            failures.append(f"answer case did not use live model (mode={result['mode']})")
        if not grounding_safe:
            failures.append(f"grounding safety failure: {grounding_failures}")
        if result["http_status"] not in (None, 200):
            failures.append(f"API returned HTTP {result['http_status']}")

        case_pass = not failures
        if case.get("critical") and not case_pass:
            critical_failure_ids.append(case["id"])

        checks = {
            "intent": intent_pass,
            "scope": scope_pass,
            "clarification": clarification_pass,
            "behavior": behavior_pass,
            "ta_handoff": ta_pass,
            "decision": decision_pass,
            "citation": citation_pass,
            "content": content_pass,
            "claim_grounding": claim_grounding_pass,
            "case": case_pass,
        }
        for key, passed in checks.items():
            counters[key] += int(passed)

        if expected["behavior"] == "answer":
            answer_case_count += 1
            live_answer_passed += int(case_pass)
        if expected.get("claims"):
            claim_case_count += 1
            claim_case_passed += int(content_pass)

        category = case["category"]
        category_breakdown.setdefault(category, {"total": 0, "passed": 0})
        category_breakdown[category]["total"] += 1
        category_breakdown[category]["passed"] += int(case_pass)

        case_details.append({
            "id": case["id"],
            "category": category,
            "origin": case.get("origin", ""),
            "tags": case.get("tags", []),
            "critical": bool(case.get("critical")),
            "query": case["query"],
            "expected_intent": expected["intent"],
            "actual_intent": result["intent"],
            "expected_scope": expected["scope"],
            "actual_scope": result["scope"],
            "expected_clarification": expected["needs_clarification"],
            "actual_clarification": result["needs_clarification"],
            "expected_behavior": expected["behavior"],
            "actual_behavior": actual_behavior,
            "expected_ta_handoff": ta_expected,
            "actual_ta_handoff": result["ta_handoff_suggested"],
            "decision_pass": decision_pass,
            "citation_pass": citation_pass,
            "content_pass": content_pass,
            "claim_grounding_pass": claim_grounding_pass,
            "claim_details": claim_details,
            "grounding_safe": grounding_safe,
            "retrieved_sources": result["retrieved_sources"],
            "sources_cited": result["sources"],
            "mode": result["mode"],
            "model": result["model"],
            "answer": result["answer"],
            "error": result["error"],
            "case_pass": case_pass,
            "failures": failures,
            "latency_ms": result["latency_ms"],
        })
        print(f"{case['id']}: {'PASS' if case_pass else 'FAIL'} ({result['mode']}, {result['latency_ms']}ms)")

    total = len(cases)
    observed_count = sum(
        1
        for case in cases
        if case.get("origin", "").startswith(("chatlog", "field_observation", "product_pain"))
    )
    verbatim_count = sum(
        1
        for case in cases
        if "verbatim" in case.get("origin", "") or case.get("origin", "").startswith("field_observation")
    )
    summary = {
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "evaluator_version": EVALUATOR_VERSION,
        "version": dataset["version"],
        "transport": transport,
        "total_cases": total,
        "observed_case_count": observed_count,
        "verbatim_case_count": verbatim_count,
        "eval_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_provider": active_provider,
        "active_model": active_model,
        "quality_bar": dataset["quality_bar"],
        "passed_cases": counters["case"],
        "overall_pass_percent": _format_rate(counters["case"], total),
        "intent_accuracy_percent": _format_rate(counters["intent"], total),
        "scope_accuracy_percent": _format_rate(counters["scope"], total),
        "clarification_accuracy_percent": _format_rate(counters["clarification"], total),
        "behavior_accuracy_percent": _format_rate(counters["behavior"], total),
        "ta_handoff_accuracy_percent": _format_rate(counters["ta_handoff"], total),
        "decision_pass_percent": _format_rate(counters["decision"], total),
        "live_answer_pass_percent": _format_rate(live_answer_passed, answer_case_count),
        "citation_grounding_percent": _format_rate(
            sum(
                1
                for detail in case_details
                if detail["expected_behavior"] == "answer"
                and detail["citation_pass"]
                and detail["claim_grounding_pass"]
            ),
            answer_case_count,
        ),
        "claim_coverage_percent": _format_rate(claim_case_passed, claim_case_count),
        "critical_failure_count": len(critical_failure_ids),
        "critical_failure_ids": critical_failure_ids,
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
    bars = dataset["quality_bar"]
    summary["quality_checks"] = {
        "overall": summary["overall_pass_percent"] >= bars["overall_pass_percent"],
        "decision": summary["decision_pass_percent"] >= bars["decision_pass_percent"],
        "live_answer": summary["live_answer_pass_percent"] >= bars["live_answer_pass_percent"],
        "citation_grounding": (
            summary["citation_grounding_percent"] >= bars["citation_grounding_percent"]
        ),
        "critical": summary["critical_failure_count"] <= bars["max_critical_failures"],
        "latency": summary["live_latency"]["p90_ms"] < 12000,
    }

    if write_outputs:
        version_slug = dataset["version"].split(".")[0]
        json_out = EVAL_DIR / f"eval_golden_set_v{version_slug}_results.json"
        report_out = EVAL_DIR / f"EVAL_REPORT_V{version_slug}.md"
        json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        report_out.write_text(generate_markdown_report(summary), encoding="utf-8")

    print(
        f"Completed: {summary['passed_cases']}/{total} passed, "
        f"decision {summary['decision_pass_percent']}%, "
        f"citation grounding {summary['citation_grounding_percent']}%, "
        f"critical failures {summary['critical_failure_count']}"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a versioned VLearn golden-set evaluation.")
    parser.add_argument("--version", choices=("v2", "v3"), default="v3")
    parser.add_argument("--dataset", help="Optional path to a custom golden-set JSON file.")
    parser.add_argument("--transport", choices=("api", "direct"), default="api")
    parser.add_argument("--provider", help="Provider override, for example nvidia or gemini.")
    parser.add_argument("--no-write", action="store_true", help="Do not update report/result artifacts.")
    args = parser.parse_args()
    run_golden_set_eval(
        version=args.version,
        dataset_path=args.dataset,
        transport=args.transport,
        provider_name=args.provider,
        write_outputs=not args.no_write,
    )


if __name__ == "__main__":
    main()
