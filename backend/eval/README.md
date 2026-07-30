# Versioned evaluation

The evaluation artifacts are versioned so a new test design does not rewrite an
older score.

| Version | Role | Dataset | Result |
|---|---|---|---|
| v2 | Frozen implementation regression set | `golden_set_v2.json` | `EVAL_REPORT_V2.md` |
| v3 | Robustness and API-workflow baseline | `golden_set_v3.json` | `EVAL_REPORT_V3.md` |

## Run

From `backend/`:

```powershell
.\.venv\Scripts\python.exe eval_golden_set.py --version v3 --transport api
```

Useful variants:

```powershell
# Re-run the frozen v2 set without overwriting its committed result.
.\.venv\Scripts\python.exe eval_golden_set.py --version v2 --transport api --no-write

# Exercise the internal functions when debugging; this is not the submission score.
.\.venv\Scripts\python.exe eval_golden_set.py --version v3 --transport direct --no-write
```

## Version policy

- Never edit a released dataset to make current code pass.
- Fixing a scorer bug may regenerate the same version, but the evaluator version
  and dataset SHA-256 in the report must identify the exact run.
- Changing expected product behavior or adding/removing cases creates the next
  dataset version.
- Keep failed cases in the committed report. The gap to the quality gates is the
  product backlog, not a reason to lower the gates.
- `v2` remains useful for regression; `v3` is the stronger measure of generalization.

## What v3 measures

- The real FastAPI `/api/v1/companion/chat` workflow, including response schema,
  clarification state and TA handoff suggestion.
- Paraphrases, typos, colloquial Vietnamese and mixed English/Vietnamese.
- Missing evidence even when the current slide itself was retrieved.
- Claim coverage and claim-level citation grounding against human-labelled sources.
- Critical no-fail cases for fabricated logistics, graded assessments, credentials
  and prompt attacks.

Automatic claim matching is still an approximation. Human review remains required
for semantic correctness, especially on long document and session summaries.
