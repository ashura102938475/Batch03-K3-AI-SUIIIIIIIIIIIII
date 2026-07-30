"""Lấy đúng chunk theo phạm vi đã nhận diện.

Phỏng theo `tools/policy/tool.py` của Day04 Lab: parse YAML frontmatter, chia section
theo heading `## `, chấm điểm bằng term-overlap có trọng số, và giữ nguyên trust
boundary tách dòng đáng ngờ ra khỏi phần facts.

Nguồn:
  - Slide     : PDF (`*.pdf`) & Markdown (`*.md`) trong `backend/corpus/`
  - Transcript: `transcript-*.md` trong `backend/corpus/` hoặc từ data pack.
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
DATA_SLIDES_DIR = ROOT.parent / "data" / "vlearn-pack" / "slides"
DEFAULT_TRANSCRIPT = ROOT.parent / "data" / "vlearn-pack" / "transcript" / "transcript-04-clean.md"

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
    """Load slides from Markdown and PDF files in CORPUS_DIR."""
    chunks: list[Chunk] = []

    # 1. Parse markdown slides
    for path in sorted(CORPUS_DIR.glob("*.md")) if CORPUS_DIR.exists() else []:
        if path.name.startswith("transcript") or path.name.lower() == "readme.md":
            continue
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if not meta.get("day"):
            continue
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

    # 2. Parse PDF slides from repo corpus and supplied data pack without copying data.
    pdf_paths: list[Path] = []
    for directory in (CORPUS_DIR, DATA_SLIDES_DIR):
        if directory.exists():
            pdf_paths.extend(sorted(directory.glob("*.pdf")))

    for path in pdf_paths:
        doc_id = path.name
        title = path.stem
        day_match = re.search(r"d(\d+)", path.name, re.IGNORECASE)
        day = f"day0{day_match.group(1)}" if day_match else "day01"
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            for page_idx, page in enumerate(reader.pages, start=1):
                raw_text = page.extract_text() or ""
                facts, untrusted = _split_trusted(raw_text)
                if not facts.strip():
                    continue
                chunks.append(Chunk(
                    chunk_id=f"{doc_id}#p{page_idx}",
                    day=day, doc_id=doc_id, title=title, page=page_idx,
                    cite=f"Trang {page_idx}", text=facts, kind="slide", untrusted=untrusted,
                ))
        except Exception:
            pass

    return chunks


def transcript_path() -> Path:
    override = os.getenv("VLEARN_TRANSCRIPT_PATH", "").strip()
    return Path(override).expanduser() if override else DEFAULT_TRANSCRIPT


def load_transcript() -> list[Chunk]:
    """Đọc tất cả transcript trong CORPUS_DIR hoặc transcript_path()."""
    chunks: list[Chunk] = []
    paths: list[Path] = sorted(CORPUS_DIR.glob("transcript-*.md"))
    if not paths and transcript_path().exists():
        paths = [transcript_path()]

    for path in paths:
        day_match = re.search(r"transcript-0?(\d+)", path.name)
        day_code = f"day0{day_match.group(1)}" if day_match else TRANSCRIPT_DAY

        current_code: str | None = None
        buffer: list[str] = []

        def flush() -> None:
            if not current_code or not buffer:
                return
            facts, untrusted = _split_trusted("\n".join(buffer))
            if not facts:
                return
            chunks.append(Chunk(
                chunk_id=current_code, day=day_code, doc_id=path.name,
                title=f"Transcript {day_code.upper()}", page=None, cite=current_code,
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


def _compare_terms(query: str) -> set[str]:
    folded = fold_text(query)
    cleaned = re.sub(r"\b(so sanh|phan biet|khac nhau|giong nhau|khac gi|voi|va|vs|versus|trong|tai lieu|slide|trang|nay|la gi)\b", " ", folded)
    return {term for term in terms(cleaned) if len(term) > 2}


def _ordered_representative(pool: list[Chunk], limit: int) -> list[Chunk]:
    slides = [c for c in pool if c.kind == "slide" and c.page is not None]
    if not slides:
        return sorted(pool, key=lambda c: (c.page is None, c.page or 0))[:limit]
    by_page: dict[int, Chunk] = {}
    for chunk in sorted(slides, key=lambda c: c.page or 0):
        if chunk.page is not None and chunk.page not in by_page:
            by_page[chunk.page] = chunk
    pages = list(by_page)
    if len(pages) <= limit:
        return [by_page[p] for p in pages]
    step = max(1, len(pages) // limit)
    sampled = pages[::step][:limit]
    if pages[-1] not in sampled:
        sampled[-1] = pages[-1]
    return [by_page[p] for p in sampled]


def search(query: str, scope_result, chunks: list[Chunk], *, selection: str = "", top_k: int = 6, task: str | None = None) -> list[Chunk]:
    scope = scope_result.scope

    if scope in ("out_of_scope", "ambiguous"):
        return []

    if scope == "selected_text":
        if not selection.strip():
            return []
        page = scope_result.target_page
        cite = f"Trang {page} · đoạn bôi đen" if page is not None else "Trang hiện tại · đoạn bôi đen"
        return [Chunk(
            chunk_id="selection", day=scope_result.target_day or "", doc_id="đoạn bôi đen",
            title="Đoạn bạn đang bôi đen", page=page,
            cite=cite,
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

    if task == "summary" and scope in ("current_document", "whole_session"):
        return _ordered_representative(pool, top_k)

    query_terms = terms(query)
    folded_query = fold_text(query)
    asks_definition = task == "definition" or any(signal in folded_query for signal in (" la gi", "nghia la", "khai niem"))
    compare_terms = _compare_terms(query) if task == "compare" else set()
    for chunk in pool:
        title_terms = terms(f"{chunk.title} {chunk.doc_id}")
        body_terms = terms(chunk.text)
        chunk.score = len(query_terms & body_terms) + 3 * len(query_terms & title_terms)
        if asks_definition:
            folded_body = fold_text(chunk.text)
            for term in query_terms:
                if f"{term} la gi" in folded_body or f"khai niem {term}" in folded_body:
                    chunk.score += 8
                elif term in body_terms and any(signal in folded_body for signal in ("la mot", "model nen", "mo hinh", "dinh nghia")):
                    chunk.score += 2
        if task == "compare" and compare_terms:
            hits = compare_terms & body_terms
            chunk.score += 4 * len(hits)
            if len(hits) >= 2:
                chunk.score += 8
        if task in ("quiz", "misconception"):
            folded_body = fold_text(chunk.text)
            if any(signal in folded_body for signal in ("khong phai", "luu y", "nham", "khac", "vi du", "la mot")):
                chunk.score += 3

    if all(chunk.score == 0 for chunk in pool):
        ordered = sorted(pool, key=lambda c: (c.page is None, c.page or 0))
    else:
        ordered = sorted(pool, key=lambda c: c.score, reverse=True)
    return ordered[:top_k]
