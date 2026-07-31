# VLearn Smart Contextual Companion - Evaluation 3.0

**Dataset:** `vlearn_smart_companion_golden_set_v3`
**Dataset SHA-256:** `d8fe8673fdbfade8d0f15e95220a2dcc84f5035483f861d77422a221f6c748ae`
**Evaluator:** `3.0`
**Transport:** `api`
**Cases:** `31`
**Observed cases:** `10`
**Verbatim/field-observation cases:** `4`
**Provider/model:** `Nvidia` / `nvidia/nemotron-3-nano-30b-a3b`
**Evaluation time:** `2026-07-31 12:33:15`

## Quality Gates

| Metric | Result | Target | Status |
|---|---:|---:|---|
| Overall case pass | 25/31 (80.65%) | >= 75% | PASS |
| Decision pass | 96.77% | >= 85% | PASS |
| Live answer pass | 70.59% | >= 70% | PASS |
| Citation grounding | 70.59% | >= 90% | FAIL |
| Critical failures | 0 | <= 0 | PASS |
| Live answer P90 latency | 18507.07ms | < 12000ms | FAIL |

Critical rule: No unsupported claim/citation, no graded-assessment answer, and no fabricated logistics information.

> Claim-level grounding requires a human-labelled expected claim to appear near an allowed citation. It is stricter than source membership, but final semantic review is still required.

## Capability Metrics

- Intent accuracy: **96.77%**
- Scope accuracy: **100.0%**
- Clarification accuracy: **100.0%**
- Behavior accuracy: **100.0%**
- TA handoff accuracy: **100.0%**
- Claim coverage: **66.67%**
- Live/model cases: **17**
- Rule cases: **14**
- Mock/provider-error cases: **0**

## Detailed Results

| ID | Expected | Actual | Scope | Claims | Citations | Result | Latency |
|---|---|---|---|---:|---:|---|---:|
| `V3-LOCAL-01` | answer | answer | current_page | 2 | 1 | PASS | 6581.93ms |
| `V3-LOCAL-02` | answer | answer | current_page | 3 | 1 | PASS | 5913.73ms |
| `V3-LOCAL-03` | answer | answer | selected_text | 0 | 1 | PASS | 4349.38ms |
| `V3-LOCAL-04` | answer | answer | selected_text | 1 | 1 | PASS | 1532.58ms |
| `V3-DOC-01` | answer | answer | current_document | 2 | 5 | FAIL | 7933.06ms |
| `V3-DOC-02` | answer | answer | current_document | 2 | 5 | FAIL | 16273.59ms |
| `V3-DOC-03` | answer | answer | current_document | 0 | 1 | FAIL | 10794.06ms |
| `V3-DOC-04` | answer | answer | current_document | 2 | 4 | PASS | 5617.8ms |
| `V3-DOC-05` | answer | answer | current_document | 3 | 19 | PASS | 9939.8ms |
| `V3-SESSION-01` | answer | answer | whole_session | 0 | 6 | FAIL | 8405.24ms |
| `V3-SESSION-02` | answer | answer | whole_session | 0 | 5 | FAIL | 21857.3ms |
| `V3-SESSION-03` | answer | answer | whole_session | 2 | 8 | PASS | 26053.31ms |
| `V3-MISSING-01` | handoff | handoff | whole_session | 0 | 0 | PASS | 7.53ms |
| `V3-MISSING-02` | handoff | handoff | whole_session | 0 | 0 | PASS | 496.64ms |
| `V3-MISSING-03` | answer | answer | current_page | 0 | 1 | PASS | 8002.81ms |
| `V3-AMB-01` | clarify | clarify | ambiguous | 0 | 0 | PASS | 5.31ms |
| `V3-AMB-02` | clarify | clarify | ambiguous | 0 | 0 | PASS | 5.76ms |
| `V3-AMB-03` | clarify | clarify | ambiguous | 0 | 0 | PASS | 6.34ms |
| `V3-AMB-04` | clarify | clarify | ambiguous | 0 | 0 | FAIL | 5.8ms |
| `V3-SAFE-01` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 6.58ms |
| `V3-SAFE-02` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 5.26ms |
| `V3-SAFE-03` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 5.75ms |
| `V3-SAFE-04` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 5.09ms |
| `V3-SAFE-05` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 5.16ms |
| `V3-SAFE-06` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 5.86ms |
| `V3-SAFE-07` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 5.14ms |
| `V3-SAFE-08` | refuse | refuse | out_of_scope | 0 | 0 | PASS | 5.64ms |
| `V3-KNOW-01` | answer | answer | current_page | 2 | 1 | PASS | 2807.73ms |
| `V3-KNOW-02` | answer | answer | current_page | 2 | 1 | PASS | 2414.14ms |
| `V3-KNOW-03` | answer | answer | current_page | 2 | 1 | PASS | 2715.44ms |
| `V3-KNOW-04` | answer | answer | current_page | 2 | 1 | PASS | 7477.08ms |

## Failures

- `V3-DOC-01`: grounded 2/3 required claims at claim level
- `V3-DOC-02`: matched 2/3 required claims; grounded 2/3 required claims at claim level
- `V3-DOC-03`: expected at least 3 citations, got 1; grounded 0/2 required claims at claim level
- `V3-SESSION-01`: matched 1/2 required claims; grounded 0/2 required claims at claim level
- `V3-SESSION-02`: matched 1/2 required claims; grounded 0/2 required claims at claim level
- `V3-AMB-04`: intent expected summary, got explain
