---
title: 'VLearn Companion 5-Stage REST API Pipeline'
type: 'feature'
created: '2026-07-30'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['spec.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** The VLearn Smart Contextual Companion requires a structured REST API pipeline exposing the 5 distinct stages (Detect Intent, Detect Scope, Retrieve Context, Generate Grounded Response, Fallback & TA Escalation) for frontend integration and automated evaluation.

**Approach:** Implement FastAPI endpoints in `codebase/backend/api.py` serving each individual pipeline stage (`/api/v1/detect-intent`, `/api/v1/detect-scope`, `/api/v1/retrieve-context`, `/api/v1/generate-response`) plus the unified end-to-end `/api/v1/companion/chat` and `/api/v1/escalate-ta` endpoints.

## Boundaries & Constraints

**Always:**
- Keep Intent and Scope Detection 100% deterministic (rule-based, zero LLM cost).
- Structure responses strictly in Vietnamese with inline citations `[Trang N]` / `[Txx-NNN]`.
- Provide a `sources_used` field in response objects.
- Maintain fallback to offline Mock mode with `🟡 MOCK` badge when API key is missing or quota is exhausted.

**Block If:**
- Upstream requirements demand breaking existing retrieval signature or removing trace logging.

**Never:**
- Call LLM for out-of-scope refusals or scope detection.
- Commit raw data pack files to version control.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY_PATH | `POST /api/v1/companion/chat` with clear query | `200 OK` + grounded Vietnamese answer + sources list + turn trace written | Fallback to mock on LLM exception |
| AMBIGUOUS_SCOPE | Query: "Tóm tắt bài này đi" | `200 OK` + `needs_clarification: true` + 3 scope options | Prompt user for scope selection |
| OUT_OF_SCOPE | Query: "Cho tôi admin password" | `200 OK` + graceful refusal + TA handoff suggestion | No LLM call executed |
| ESCALATE_TA | `POST /api/v1/escalate-ta` | `200 OK` + `status: escalated` | Return JSON confirmation |

</intent-contract>

## Code Map

- `codebase/backend/api.py` -- FastAPI server application with OpenAPI schemas and endpoints for all 5 stages
- `codebase/backend/companion/scope.py` -- Deterministic intent & scope classification engine
- `codebase/backend/companion/retriever.py` -- Scope-aware PDF & transcript chunk retrieval
- `codebase/backend/companion/answer.py` -- Grounded QA response generator with citation formatting
- `codebase/backend/companion/trace.py` -- Turn trace recorder (`runs/turn_*.json`)

## Tasks & Acceptance

**Execution:**
- `codebase/backend/api.py` -- Define Pydantic request/response schemas and endpoints (`/api/v1/detect-intent`, `/api/v1/detect-scope`, `/api/v1/retrieve-context`, `/api/v1/generate-response`, `/api/v1/companion/chat`, `/api/v1/escalate-ta`).
- `codebase/backend/companion/retriever.py` -- Parse real PDF slide pages and clean transcript files into 751 corpus chunks.
- `codebase/backend/providers/nvidia_provider.py` -- Integrate NVIDIA Provider as default LLM provider.

**Acceptance Criteria:**
- Given a valid query, when calling `POST /api/v1/companion/chat`, then backend returns `200 OK` with grounded answer, active model, sources list, and trace log filename.
- Given an ambiguous query, when calling `POST /api/v1/companion/chat`, then backend returns `needs_clarification: true` with 3 scope options.

## Verification

**Commands:**
- `uv run python -m uvicorn api:app --host 0.0.0.0 --port 8000` -- expected: `FastAPI server running live`
- `uv run python -c "from fastapi.testclient import TestClient; from api import app; c = TestClient(app); assert c.get('/health').status_code == 200"` -- expected: `200 OK`
