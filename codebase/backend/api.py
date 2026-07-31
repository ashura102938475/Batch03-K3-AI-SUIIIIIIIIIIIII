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

from companion.answer import REFUSAL_ASSESSMENT, REFUSAL_OUT_OF_SCOPE, generate
from companion.classify import classify_turn
from companion.retriever import Chunk, load_corpus, search as corpus_search, transcript_paths
from companion.routing import should_suggest_ta, should_try_external
from companion.safety import external_support_policy, screen_query
from companion.scope import ScopeResult, detect_intent, detect_scope
from companion.ta_notifier import notify_ta_channel
from companion.trace import build_record, write_turn_trace
from providers import make_provider


app = FastAPI(
    title="VLearn Smart Contextual Companion API",
    description="REST API mapping proposed pipeline: Intent Detection -> Scope Detection -> Context Retrieval -> Grounded Generation -> Fallback & TA Escalation",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# ===================================================================== SCHEMAS

IntentType = Literal["conversation", "summary", "explain", "logistics", "out_of_scope", "prompt_attack"]
ScopeType = Literal[
    "conversation",
    "selected_text",
    "current_page",
    "current_document",
    "whole_session",
    "external_knowledge",
    "ambiguous",
    "out_of_scope",
]


class DetectIntentRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Student query text")


class DetectIntentResponse(BaseModel):
    query: str
    intent: IntentType
    description: str


class DetectScopeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    current_day: str = "day01"
    current_page: int = 1
    selection: str = ""
    # Tắt để lấy kết quả thuần luật, tất định — dùng khi cần truy lỗi định tuyến.
    use_llm: bool = True


class DetectScopeResponse(BaseModel):
    query: str
    scope: ScopeType
    scope_label: str
    confidence: Literal["cao", "trung bình", "thấp"]
    reason: str
    target_day: str
    target_page: int
    needs_clarification: bool


class RetrieveContextRequest(BaseModel):
    query: str = Field(..., min_length=1)
    scope: ScopeType
    current_day: str = "day01"
    current_page: int = 1
    selection: str = ""
    top_k: int = 6


class ContextChunkItem(BaseModel):
    chunk_id: str
    day: str
    doc_id: str
    title: str
    page: int | None
    cite: str
    text: str
    kind: str


class RetrieveContextResponse(BaseModel):
    scope: ScopeType
    strategy_used: str
    count: int
    chunks: list[ContextChunkItem]


class GenerateResponseRequest(BaseModel):
    query: str = Field(..., min_length=1)
    scope: ScopeType
    chunks: list[ContextChunkItem]
    provider: str | None = None
    model: str | None = None


class CitationPayload(BaseModel):
    label: str
    kind: str
    title: str
    source_id: str
    day: str | None = None
    page: int | None = None
    url: str | None = None
    excerpt: str


class GroundedAnswerPayload(BaseModel):
    text: str
    sources_used: list[str]
    citations: list[CitationPayload]
    mode: str
    model: str | None
    latency_ms: int
    error: str | None


class ChatPipelineRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Student question")
    current_day: str = "day01"
    current_page: int = 1
    selection: str = ""
    forced_scope: ScopeType | None = None
    provider: str | None = None
    model: str | None = None


class ClarificationOption(BaseModel):
    label: str
    scope: ScopeType


class ChatPipelineResponse(BaseModel):
    query: str
    intent: IntentType
    scope: ScopeType
    scope_label: str
    confidence: str
    needs_clarification: bool
    clarification_options: list[ClarificationOption] | None = None
    sources_used: list[str]
    citations: list[CitationPayload]
    answer: str
    mode: str
    model: str | None
    latency_ms: int
    trace_file: str
    ta_handoff_suggested: bool


class TAHandoffRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    student_query: str = Field(..., min_length=1)
    current_day: str = "day01"
    current_page: int = Field(1, ge=1)


class TAHandoffResponse(BaseModel):
    status: str
    pushed: bool
    delivery_status: str
    reason: str
    student_query: str
    current_day: str
    current_page: int
    message: str


def build_citation_payloads(answer: dict[str, Any], chunks: list[Chunk]) -> list[CitationPayload]:
    """Return only citations that map to a retrieved chunk or Tavily result."""
    if not str(answer.get("text") or "").strip() or answer.get("mode") == "guardrail":
        return []

    payloads: list[CitationPayload] = []
    seen: set[tuple[str, str]] = set()
    external_sources = answer.get("external_sources", [])

    for source_value in answer.get("sources", []):
        if source_value.startswith(("http://", "https://")):
            external = next(
                (item for item in external_sources if item.get("url") == source_value),
                None,
            )
            if not external:
                continue
            source_index = external_sources.index(external) + 1
            key = ("web", source_value)
            if key in seen:
                continue
            seen.add(key)
            payloads.append(CitationPayload(
                label=f"Nguồn {source_index}",
                kind="web",
                title=external.get("title") or source_value,
                source_id=source_value,
                url=source_value,
                excerpt=" ".join((external.get("snippet") or "").split())[:220],
            ))
            continue

        chunk = next((item for item in chunks if item.cite == source_value), None)
        if not chunk:
            continue
        key = (chunk.kind, source_value)
        if key in seen:
            continue
        seen.add(key)
        payloads.append(CitationPayload(
            label=source_value,
            kind=chunk.kind,
            title=chunk.title,
            source_id=chunk.doc_id,
            day=chunk.day,
            page=chunk.page,
            excerpt=" ".join(chunk.text.split())[:220],
        ))

    return payloads


def source_values(citations: list[CitationPayload]) -> list[str]:
    return [citation.url or citation.label for citation in citations]


# ===================================================================== ENDPOINTS

@app.get("/")
@app.get("/health")
def health_check() -> dict[str, Any]:
    provider = get_active_provider()
    provider_type = provider.__class__.__name__.replace("Provider", "") if provider else "MOCK"
    corpus_by_day = {
        day: {
            "slides": sum(1 for chunk in CORPUS if chunk.day == day and chunk.kind == "slide"),
            "transcripts": sum(1 for chunk in CORPUS if chunk.day == day and chunk.kind == "transcript"),
        }
        for day in sorted({chunk.day for chunk in CORPUS})
    }
    return {
        "status": "online",
        "active_provider": provider_type,
        "default_model": getattr(provider, "default_model", None) if provider else os.getenv("NVIDIA_MODEL"),
        # Phơi ra để một default chết (model không tồn tại -> 404) không âm thầm vô hiệu
        # hoá cả tầng phân loại nhanh như đã từng xảy ra với google/gemma-3-1b-it.
        "fast_model": os.getenv("NVIDIA_FAST_MODEL", "meta/llama-3.1-8b-instruct"),
        "external_support_policy": external_support_policy(),
        "corpus_chunks_loaded": len(CORPUS),
        "transcript_files_loaded": len(transcript_paths()),
        "corpus_by_day": corpus_by_day,
    }


# 1. DETECT INTENT
@app.post("/api/v1/detect-intent", response_model=DetectIntentResponse)
def detect_intent_api(req: DetectIntentRequest) -> DetectIntentResponse:
    # Đi qua cùng một điểm vào với pipeline, nếu không endpoint lẻ sẽ nói một đằng
    # còn /companion/chat làm một nẻo.
    intent_str = classify_turn(
        req.query,
        has_selection=False,
        current_day="day01",
        current_page=1,
        provider=get_active_provider(),
    ).intent
    intent_desc = {
        "summary": "Nhu cầu tóm tắt/tổng hợp nội dung",
        "explain": "Nhu cầu giải thích khái niệm/bài tập",
        "logistics": "Hỏi về link/deadline/file download",
        "out_of_scope": "Ngoài phạm vi môn học",
        "prompt_attack": "Yêu cầu không an toàn / prompt injection",
    }.get(intent_str, "Nhu cầu hỏi đáp thông thường")
    return DetectIntentResponse(query=req.query, intent=intent_str, description=intent_desc)


# 2. DETECT SCOPE
@app.post("/api/v1/detect-scope", response_model=DetectScopeResponse)
def detect_scope_api(req: DetectScopeRequest) -> DetectScopeResponse:
    scope_res = classify_turn(
        req.query,
        has_selection=bool(req.selection.strip()),
        current_day=req.current_day,
        current_page=req.current_page,
        provider=get_active_provider() if req.use_llm else None,
        use_llm=req.use_llm,
    ).scope_result
    return DetectScopeResponse(
        query=req.query,
        scope=scope_res.scope,
        scope_label=scope_res.label,
        confidence=scope_res.confidence,
        reason=scope_res.reason,
        target_day=scope_res.target_day or req.current_day,
        target_page=scope_res.target_page or req.current_page,
        needs_clarification=scope_res.needs_clarification,
    )


# 3. RETRIEVE CONTEXT
@app.post("/api/v1/retrieve-context", response_model=RetrieveContextResponse)
def retrieve_context_api(req: RetrieveContextRequest) -> RetrieveContextResponse:
    scope_res = detect_scope(
        req.query,
        has_selection=bool(req.selection.strip()),
        current_day=req.current_day,
        current_page=req.current_page,
    )
    scope_res.scope = req.scope

    strategy_map = {
        "selected_text": "Dùng đoạn bôi đen + trang hiện tại",
        "current_page": "Dùng nội dung slide trang hiện tại",
        "current_document": "Dùng outline / tóm tắt các trang trong file PDF",
        "whole_session": "Dùng slide nhiều trang cùng Day + clean transcript liên quan",
        "external_knowledge": "Tra cứu nguồn web có citation bằng Tavily",
        "ambiguous": "Chờ xác nhận phạm vi từ người học",
        "out_of_scope": "Bỏ qua retrieval (ngoài phạm vi)",
    }

    chunks = corpus_search(req.query, scope_res, CORPUS, selection=req.selection, top_k=req.top_k)
    items = [
        ContextChunkItem(
            chunk_id=c.chunk_id,
            day=c.day,
            doc_id=c.doc_id,
            title=c.title,
            page=c.page,
            cite=c.cite,
            text=c.text,
            kind=c.kind,
        )
        for c in chunks
    ]
    return RetrieveContextResponse(
        scope=req.scope,
        strategy_used=strategy_map.get(req.scope, "Dùng nội dung mặc định"),
        count=len(items),
        chunks=items,
    )


# 4. GENERATE GROUNDED RESPONSE
@app.post("/api/v1/generate-response", response_model=GroundedAnswerPayload)
def generate_response_api(req: GenerateResponseRequest) -> GroundedAnswerPayload:
    provider = get_active_provider(req.provider)
    scope_res = detect_scope(req.query, has_selection=False, current_day="day01", current_page=1)
    scope_res.scope = req.scope

    chunks = [
        Chunk(
            chunk_id=c.chunk_id,
            day=c.day,
            doc_id=c.doc_id,
            title=c.title,
            page=c.page,
            cite=c.cite,
            text=c.text,
            kind=c.kind,
        )
        for c in req.chunks
    ]

    answer = generate(req.query, scope_res, chunks, provider=provider, model=req.model)
    citations = build_citation_payloads(answer, chunks)
    return GroundedAnswerPayload(
        text=answer["text"],
        sources_used=source_values(citations),
        citations=citations,
        mode=answer["mode"],
        model=answer["model"],
        latency_ms=answer["latency_ms"],
        error=answer["error"],
    )


# 5. FULL PIPELINE (END-TO-END CHAT)
@app.post("/api/v1/companion/chat", response_model=ChatPipelineResponse)
def full_chat_pipeline(req: ChatPipelineRequest) -> ChatPipelineResponse:
    provider = get_active_provider(req.provider)
    decision = classify_turn(
        req.query,
        has_selection=bool(req.selection.strip()),
        current_day=req.current_day,
        current_page=req.current_page,
        provider=provider,
    )
    intent = decision.intent
    scope_res = decision.scope_result

    if req.forced_scope:
        scope_res.scope = req.forced_scope
        scope_res.confidence = "cao"
        scope_res.reason = "Bạn đã chọn phạm vi này khi mình hỏi lại."
        scope_res.origin = "forced"

    chunks = corpus_search(req.query, scope_res, CORPUS, selection=req.selection)
    if (
        scope_res.scope != "external_knowledge"
        and should_try_external(req.query, scope_res, chunks)
    ):
        scope_res = ScopeResult(
            scope="external_knowledge",
            confidence="cao",
            reason="Không thấy nội dung liên quan trên trang hiện tại nên Tutor chuyển sang tra cứu nguồn web.",
            target_day=req.current_day,
            target_page=req.current_page,
        )
        chunks = []

    answer = generate(req.query, scope_res, chunks, provider=provider, model=req.model)
    if (
        scope_res.scope != "external_knowledge"
        and should_try_external(req.query, scope_res, chunks, answer["text"])
    ):
        scope_res = ScopeResult(
            scope="external_knowledge",
            confidence="cao",
            reason="Nguồn slide không đủ trả lời nên Tutor đã tra cứu kiến thức bổ sung có citation.",
            target_day=req.current_day,
            target_page=req.current_page,
        )
        chunks = []
        answer = generate(req.query, scope_res, chunks, provider=provider, model=req.model)

    citations = build_citation_payloads(answer, chunks)

    # ---- Lớp phòng thủ cuối: câu không được phép trả lời thì không được mang citation.
    # Bốn critical failure của v3 đều cùng một hình dạng: định tuyến sai -> sinh câu trả
    # lời -> gắn kèm [Trang 3] khiến nó trông có căn cứ. Bất biến này khiến chuyện đó bất
    # khả thi về cấu trúc, bất kể luật hay LLM ở trên có quyết sai thế nào.
    if scope_res.scope in ("out_of_scope", "ambiguous") or intent in (
        "out_of_scope",
        "prompt_attack",
        "logistics",
    ):
        citations = []
    verdict = screen_query(req.query)
    if verdict and answer["sources"]:
        citations = []
        answer["text"] = REFUSAL_ASSESSMENT if verdict.family == "graded" else REFUSAL_OUT_OF_SCOPE
        answer["mode"] = "guardrail"

    verified_sources = source_values(citations)
    answer["sources"] = verified_sources
    record = build_record(
        query=req.query,
        intent=intent,
        scope_result=scope_res,
        chunks=chunks,
        answer=answer,
        selection=req.selection,
    )
    trace_file = write_turn_trace(record)

    clarification_options = None
    if scope_res.needs_clarification:
        clarification_options = [
            ClarificationOption(label="Trang hiện tại", scope="current_page"),
            ClarificationOption(label="Cả tài liệu", scope="current_document"),
            ClarificationOption(label="Cả buổi học", scope="whole_session"),
        ]

    external_success = bool(
        scope_res.scope == "external_knowledge"
        and answer["mode"] in ("external", "mock")
        and verified_sources
    )
    suggest_ta = should_suggest_ta(
        scope=scope_res.scope,
        mode=answer["mode"],
        chunks=chunks,
        verified_sources=verified_sources,
        answer_text=answer["text"],
        external_success=external_success,
    )

    return ChatPipelineResponse(
        query=req.query,
        intent=intent,
        scope=scope_res.scope,
        scope_label=scope_res.label,
        confidence=scope_res.confidence,
        needs_clarification=scope_res.needs_clarification,
        clarification_options=clarification_options,
        sources_used=verified_sources,
        citations=citations,
        answer=answer["text"],
        mode=answer["mode"],
        model=answer["model"],
        latency_ms=answer["latency_ms"],
        trace_file=trace_file.name,
        ta_handoff_suggested=suggest_ta,
    )


# 6. ESCALATE TA
@app.post("/api/v1/escalate-ta", response_model=TAHandoffResponse)
def escalate_ta_api(req: TAHandoffRequest) -> TAHandoffResponse:
    res = notify_ta_channel(
        reason=req.reason,
        student_query=req.student_query,
        current_day=req.current_day,
        current_page=req.current_page,
    )
    return TAHandoffResponse(
        status=res["status"],
        pushed=res["pushed"],
        delivery_status=res["delivery_status"],
        reason=req.reason,
        student_query=req.student_query,
        current_day=req.current_day,
        current_page=req.current_page,
        message=res["message"],
    )


# 7. TRACE LOGS
@app.get("/api/v1/runs")
def list_runs() -> dict[str, Any]:
    runs_dir = ROOT / "runs"
    if not runs_dir.exists():
        return {"runs": []}
    files = sorted(runs_dir.glob("turn_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"runs": [f.name for f in files]}


@app.get("/api/v1/runs/{filename}")
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
