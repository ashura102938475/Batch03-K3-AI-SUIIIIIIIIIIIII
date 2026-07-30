from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env

load_lab_env(ROOT)

from companion.answer import generate
from companion.retriever import load_corpus, search as corpus_search, transcript_path
from companion.scope import detect_intent, detect_scope
from companion.trace import build_record, write_turn_trace
from providers import make_provider


app = FastAPI(
    title="VLearn Smart Contextual Companion API",
    description="Backend API for VLearn Contextual Companion (Scope Detection, Grounded RAG & TA Escalation)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global corpus & provider cache
CORPUS = load_corpus()


def get_active_provider(provider_name: str | None = None):
    name = provider_name or os.getenv("DEFAULT_PROVIDER", "nvidia")
    order = [name, "nvidia", "gemini", "openai", "openrouter", "anthropic"]
    seen = set()
    unique_order = [p for p in order if not (p in seen or seen.add(p))]

    for p_name in unique_order:
        key_name = f"{p_name.upper()}_API_KEY"
        if os.getenv(key_name):
            try:
                return make_provider(p_name)
            except Exception:
                pass
    return None


class DetectScopeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    current_day: str = "day01"
    current_page: int = 1
    selection: str = ""


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    scope: str = "current_page"
    current_day: str = "day01"
    current_page: int = 1
    selection: str = ""


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    current_day: str = "day01"
    current_page: int = 1
    selection: str = ""
    forced_scope: str | None = None
    provider: str | None = None
    model: str | None = None


class TAHandoffRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    student_query: str = Field(..., min_length=1)


@app.get("/")
@app.get("/health")
def health_check() -> dict[str, Any]:
    provider = get_active_provider()
    provider_type = provider.__class__.__name__.replace("Provider", "") if provider else "MOCK"
    default_model = getattr(provider, "default_model", None) if provider else None
    return {
        "status": "online",
        "active_provider": provider_type,
        "default_model": default_model or os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b"),
        "corpus_chunks_loaded": len(CORPUS),
        "has_transcript": transcript_path().exists(),
    }


@app.post("/api/detect-scope")
def detect_scope_endpoint(req: DetectScopeRequest) -> dict[str, Any]:
    intent = detect_intent(req.query)
    scope_res = detect_scope(
        req.query,
        has_selection=bool(req.selection.strip()),
        current_day=req.current_day,
        current_page=req.current_page,
    )
    return {
        "intent": intent,
        "scope": scope_res.scope,
        "label": scope_res.label,
        "confidence": scope_res.confidence,
        "reason": scope_res.reason,
        "target_day": scope_res.target_day,
        "needs_clarification": scope_res.needs_clarification,
    }


@app.post("/api/search")
def search_endpoint(req: SearchRequest) -> dict[str, Any]:
    scope_res = detect_scope(
        req.query,
        has_selection=bool(req.selection.strip()),
        current_day=req.current_day,
        current_page=req.current_page,
    )
    scope_res.scope = req.scope
    chunks = corpus_search(req.query, scope_res, CORPUS, selection=req.selection)
    return {
        "count": len(chunks),
        "chunks": [
            {
                "doc_id": c.doc_id,
                "page": c.page,
                "cite": c.cite,
                "text": c.text,
                "day": c.day,
            }
            for c in chunks
        ],
    }


@app.post("/api/ask")
def ask_endpoint(req: AskRequest) -> dict[str, Any]:
    provider = get_active_provider(req.provider)
    intent = detect_intent(req.query)
    scope_res = detect_scope(
        req.query,
        has_selection=bool(req.selection.strip()),
        current_day=req.current_day,
        current_page=req.current_page,
    )
    if req.forced_scope:
        scope_res.scope = req.forced_scope
        scope_res.confidence = "cao"
        scope_res.reason = "Bạn đã chọn phạm vi này khi mình hỏi lại."

    chunks = corpus_search(req.query, scope_res, CORPUS, selection=req.selection)
    answer = generate(req.query, scope_res, chunks, provider=provider, model=req.model)

    record = build_record(
        query=req.query,
        intent=intent,
        scope_result=scope_res,
        chunks=chunks,
        answer=answer,
        selection=req.selection,
    )
    trace_file = write_turn_trace(record)

    return {
        "question": req.query,
        "answer": answer,
        "intent": intent,
        "scope": scope_res.scope,
        "scope_label": scope_res.label,
        "confidence": scope_res.confidence,
        "reason": scope_res.reason,
        "needs_clarification": scope_res.needs_clarification,
        "trace_file": trace_file.name,
    }


@app.post("/api/escalate-ta")
def escalate_ta_endpoint(req: TAHandoffRequest) -> dict[str, Any]:
    return {
        "status": "escalated",
        "reason": req.reason,
        "student_query": req.student_query,
        "message": "Đã ghi nhận yêu cầu chuyển TA.",
    }


@app.get("/api/runs")
def list_runs() -> dict[str, Any]:
    runs_dir = ROOT / "runs"
    if not runs_dir.exists():
        return {"runs": []}
    files = sorted(runs_dir.glob("turn_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"runs": [f.name for f in files]}


@app.get("/api/runs/{filename}")
def get_run_trace(filename: str) -> dict[str, Any]:
    if "/" in filename or "\\" in filename or not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = ROOT / "runs" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Trace file not found")
    import json
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
