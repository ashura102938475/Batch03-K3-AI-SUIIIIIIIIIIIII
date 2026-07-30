"""Lấy đúng chunk theo phạm vi đã nhận diện.

Phỏng theo `tools/policy/tool.py` của Day04 Lab: parse YAML frontmatter, chia section
theo heading `## `, chấm điểm bằng term-overlap có trọng số, và giữ nguyên trust
boundary tách dòng đáng ngờ ra khỏi phần facts.

Hai nguồn:
  - Slide  : `corpus/*.md`  (slide GIẢ tự viết — xem corpus/README.md)
  - Transcript: đọc từ data pack của khoá qua đường dẫn tương đối, KHÔNG copy vào
    codebase/ — luật bảo mật data pack cấm commit data vào repo nộp bài.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from companion.text import fold_text, terms

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "corpus"
DEFAULT_TRANSCRIPT = ROOT.parent / "data" / "vlearn-pack" / "transcript" / "transcript-04-clean.md"

# Transcript nào thuộc buổi nào — theo bảng ánh xạ trong
# data/vlearn-pack/transcript/README.md (định vị buổi là suy đoán từ nội dung).
TRANSCRIPT_DAY = "day01"
TRANSCRIPT_CODE_PATTERN = re.compile(r"\[(T\d{2}-\d{3})\]")

SUSPICIOUS_MARKERS = ("assistant:", "system:", "developer:", "ignore ", "bo qua", "tro ly:", "quen het")


@dataclass
class Chunk:
    chunk_id: str
    day: str
    doc_id: str
    title: str
    page: int | None
    cite: str            # "Trang 12" hoặc "T04-031"
    text: str
    kind: str            # "slide" | "transcript" | "selection"
    untrusted: list[str] = field(default_factory=list)
    score: int = 0


def _split_trusted(text: str) -> tuple[str, list[str]]:
    """Tách dòng có mùi chỉ thị ra khỏi phần facts.

    Nội dung học liệu là dữ liệu, không phải mệnh lệnh. Chatlog thật có T0582 (đòi
    base64 toàn bộ nội dung) và T0794 (đòi API key) — lớp chỗ khó ③.
    """
    facts, untrusted = [], []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        folded = fold_text(stripped)
        if stripped.startswith(">") or any(marker in folded for marker in SUSPICIOUS_MARKERS):
            untrusted.append(stripped.lstrip("> ").strip())
        else:
            facts.append(stripped)
    return "\n".join(facts), untrusted


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            return dict(yaml.safe_load(parts[1]) or {}), parts[2].strip()
    return {}, raw.strip()


def load_slides() -> list[Chunk]:
    """Mỗi heading `## Trang N` trong corpus/*.md là một chunk."""
    chunks: list[Chunk] = []
    if not CORPUS_DIR.exists():
        return chunks

    for path in sorted(CORPUS_DIR.glob("*.md")):
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if not meta.get("day"):
            continue  # corpus/README.md không có frontmatter -> bỏ qua
        day = str(meta["day"])
        doc_id = str(meta.get("doc_id") or path.stem)
        title = str(meta.get("title") or path.stem)

        current_page: int | None = None
        buffer: list[str] = []

        def flush() -> None:
            if current_page is None or not buffer:
                return
            facts, untrusted = _split_trusted("\n".join(buffer))
            if not facts:
                return
            chunks.append(Chunk(
                chunk_id=f"{doc_id}#p{current_page}",
                day=day, doc_id=doc_id, title=title, page=current_page,
                cite=f"Trang {current_page}", text=facts, kind="slide", untrusted=untrusted,
            ))

        for line in body.splitlines():
            if line.startswith("## "):
                flush()
                heading = line[3:].strip()
                match = re.search(r"(\d+)", heading)
                current_page = int(match.group(1)) if match else None
                buffer = []
            else:
                buffer.append(line)
        flush()
    return chunks


def transcript_path() -> Path:
    override = os.getenv("VLEARN_TRANSCRIPT_PATH", "").strip()
    return Path(override).expanduser() if override else DEFAULT_TRANSCRIPT


def load_transcript() -> list[Chunk]:
    """Đọc transcript thật từ data pack. Thiếu file -> trả rỗng, không crash."""
    path = transcript_path()
    if not path.exists():
        return []

    chunks: list[Chunk] = []
    current_code: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if not current_code or not buffer:
            return
        facts, untrusted = _split_trusted("\n".join(buffer))
        if not facts:
            return
        chunks.append(Chunk(
            chunk_id=current_code, day=TRANSCRIPT_DAY, doc_id="transcript-04-clean.md",
            title="Transcript bài giảng", page=None, cite=current_code,
            text=facts, kind="transcript", untrusted=untrusted,
        ))

    for line in path.read_text(encoding="utf-8").splitlines():
        match = TRANSCRIPT_CODE_PATTERN.search(line)
        if match:
            flush()
            current_code = match.group(1)
            buffer = [TRANSCRIPT_CODE_PATTERN.sub("", line).strip()]
        elif current_code:
            buffer.append(line)
    flush()
    return chunks


def load_corpus() -> list[Chunk]:
    return load_slides() + load_transcript()


def available_days(chunks: list[Chunk]) -> set[str]:
    return {chunk.day for chunk in chunks}


def search(query: str, scope_result, chunks: list[Chunk], *, selection: str = "", top_k: int = 6) -> list[Chunk]:
    """Lọc theo phạm vi TRƯỚC, chấm điểm SAU.

    Lọc trước là điểm khác biệt của lát cắt này: tutor hiện tại retrieve trên toàn
    index rồi cite lung tung — 39/155 lượt summary cite trang không liên quan.
    """
    scope = scope_result.scope

    if scope == "out_of_scope":
        return []

    if scope == "selected_text":
        if not selection.strip():
            return []
        return [Chunk(
            chunk_id="selection", day=scope_result.target_day or "", doc_id="đoạn bôi đen",
            title="Đoạn bạn đang bôi đen", page=scope_result.target_page,
            cite=f"Trang {scope_result.target_page} · đoạn bôi đen",
            text=selection.strip(), kind="selection", score=99,
        )]

    day = scope_result.target_day
    if scope == "whole_session":
        pool = [c for c in chunks if c.day == day]
    elif scope == "current_document":
        pool = [c for c in chunks if c.day == day and c.kind == "slide"]
        if scope_result.page_range:
            start, end = scope_result.page_range
            pool = [c for c in pool if c.page is not None and start <= c.page <= end]
    elif scope in ("current_page", "ambiguous"):
        pool = [c for c in chunks if c.day == day and c.page == scope_result.target_page]
    else:
        pool = []

    if not pool:
        return []

    query_terms = terms(query)
    for chunk in pool:
        title_terms = terms(f"{chunk.title} {chunk.doc_id}")
        body_terms = terms(chunk.text)
        chunk.score = len(query_terms & body_terms) + 3 * len(query_terms & title_terms)

    # Hỏi chung chung ("tóm tắt trang này") thì gần như không term nào khớp — vẫn phải
    # trả nội dung trong phạm vi, nếu không sẽ tái hiện đúng lỗi "không tìm thấy".
    if all(chunk.score == 0 for chunk in pool):
        ordered = sorted(pool, key=lambda c: (c.page is None, c.page or 0))
    else:
        ordered = sorted(pool, key=lambda c: c.score, reverse=True)
    return ordered[:top_k]
