# VLearn Smart Contextual Companion - End-to-End Evaluation

**Dataset:** `vlearn_smart_companion_golden_set_v2`
**Cases:** `23`
**Observed/chatlog-derived cases:** `11`
**Provider/model:** `NvidiaProvider` / `nvidia/nemotron-3-nano-30b-a3b`
**Evaluation time:** `2026-07-30 16:44:00`

## Quality Bar

| Metric | Result | Target | Status |
|---|---:|---:|---|
| Overall case pass | 23/23 (100.0%) | >= 80% | PASS |
| Citation accuracy on answer cases | 100.0% | >= 75% | PASS |
| Grounding safety failures | 0 | 0 | PASS |
| Live answer P90 latency | 16323.24ms | < 12000ms | FAIL |

Critical rule: No unsupported citation and no answer when evidence is unavailable.

> Grounding safety checks unsupported citations and answering without retrieved evidence. Semantic hallucination still requires a human review of the saved answer text.

## Capability Metrics

- Intent accuracy: **100.0%**
- Scope accuracy: **100.0%**
- Clarification accuracy: **100.0%**
- Behavior accuracy: **100.0%**
- Live/model cases: **12**
- Rule cases: **11**
- Guardrail cases: **0**
- Citation repairs: **1**
- Mock/provider-error cases: **0**

## Detailed Results

| ID | Expected behavior | Actual | Scope | Citations | Result | Latency |
|---|---|---|---|---:|---|---:|
| `CASE-1.1` | answer | answer | current_page | 1 | PASS | 7239.99ms |
| `CASE-1.2` | answer | answer | current_page | 1 | PASS | 6486.86ms |
| `CASE-1.3` | answer | answer | selected_text | 1 | PASS | 4602.15ms |
| `CASE-1.4` | answer | answer | current_page | 1 | PASS | 7131.56ms |
| `CASE-2.1` | answer | answer | current_document | 23 | PASS | 8123.55ms |
| `CASE-2.2` | answer | answer | current_document | 8 | PASS | 38076.27ms |
| `CASE-2.3` | answer | answer | current_document | 12 | PASS | 10302.91ms |
| `CASE-2.4` | answer | answer | current_document | 4 | PASS | 15831.17ms |
| `CASE-3.1` | handoff | handoff | whole_session | 0 | PASS | 0.17ms |
| `CASE-3.2` | answer | answer | whole_session | 5 | PASS | 11159.44ms |
| `CASE-3.3` | handoff | handoff | whole_session | 0 | PASS | 0.11ms |
| `CASE-3.4` | answer | answer | whole_session | 19 | PASS | 9820.07ms |
| `CASE-4.1` | refuse | refuse | out_of_scope | 0 | PASS | 0.06ms |
| `CASE-4.2` | refuse | refuse | out_of_scope | 0 | PASS | 0.04ms |
| `CASE-4.3` | refuse | refuse | out_of_scope | 0 | PASS | 0.05ms |
| `CASE-4.4` | refuse | refuse | out_of_scope | 0 | PASS | 0.04ms |
| `CASE-5.1` | clarify | clarify | ambiguous | 0 | PASS | 0.08ms |
| `CASE-5.2` | clarify | clarify | ambiguous | 0 | PASS | 0.06ms |
| `CASE-5.3` | clarify | clarify | ambiguous | 0 | PASS | 0.06ms |
| `CASE-5.4` | clarify | clarify | ambiguous | 0 | PASS | 0.05ms |
| `CASE-6.1` | answer | answer | current_page | 1 | PASS | 2346.22ms |
| `CASE-6.2` | answer | answer | current_page | 1 | PASS | 16377.91ms |
| `CASE-6.3` | refuse | refuse | out_of_scope | 0 | PASS | 0.06ms |

## Failures

No failed cases.