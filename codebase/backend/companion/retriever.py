"""Load and retrieve the real VLearn sample corpus by learning scope."""
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
DATA_PACK_DIR = ROOT.parent / "data" / "vlearn-pack"
DEFAULT_SLIDES_DIR = DATA_PACK_DIR / "slides"
DEFAULT_TRANSCRIPT_DIR = DATA_PACK_DIR / "transcript"
DEFAULT_TRANSCRIPT = DEFAULT_TRANSCRIPT_DIR / "transcript-04-clean.md"

TRANSCRIPT_CODE_PATTERN = re.compile(r"\[(T\d{2}-\d{3})\]")
SUMMARY_QUERY_MARKERS = (
    "tom tat", "tom gon", "tong hop", "summary", "y chinh", "noi dung chinh",
    "phan chinh", "keyword", "tu khoa", "ghi chu", "note", "on tap",
)

# The clean transcript filenames are source IDs, not course day numbers.
# This mapping follows data/vlearn-pack/transcript/README.md.
TRANSCRIPT_DAY_BY_FILE = {
    "transcript-01-clean.md": "day02",
    "transcript-02-clean.md": "day02",
    "transcript-03-clean.md": "day02",
    "transcript-04-clean.md": "day01",
    "transcript-05-clean.md": "day02",
    "transcript-06-clean.md": "day01",
}

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


def _day_code(value: str | int) -> str:
    return f"day{int(value):02d}"


def slides_dir() -> Path:
    override = os.getenv("VLEARN_SLIDES_DIR", "").strip()
    return Path(override).expanduser() if override else DEFAULT_SLIDES_DIR


def load_slides() -> list[Chunk]:
    """Load local markdown fixtures and the real PDF sample decks."""
    chunks: list[Chunk] = []

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

    pdf_paths: dict[Path, Path] = {}
    for directory in (CORPUS_DIR, slides_dir()):
        if directory.exists():
            for path in directory.glob("*.pdf"):
                pdf_paths[path.resolve()] = path

    for path in sorted(pdf_paths.values(), key=lambda item: item.name):
        doc_id = path.name
        title = path.stem
        day_match = re.search(r"(?:^|[^a-z])d(?:ay)?[-_ ]?0?(\d+)", path.name, re.IGNORECASE)
        day = _day_code(day_match.group(1)) if day_match else "day01"
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
        except Exception as exc:
            raise RuntimeError(f"Cannot parse slide deck {path}: {exc}") from exc

    return chunks


def transcript_path() -> Path:
    override = os.getenv("VLEARN_TRANSCRIPT_PATH", "").strip()
    return Path(override).expanduser() if override else DEFAULT_TRANSCRIPT


def transcript_dir() -> Path:
    override = os.getenv("VLEARN_TRANSCRIPT_DIR", "").strip()
    return Path(override).expanduser() if override else DEFAULT_TRANSCRIPT_DIR


def transcript_paths() -> list[Path]:
    file_override = os.getenv("VLEARN_TRANSCRIPT_PATH", "").strip()
    if file_override:
        path = Path(file_override).expanduser()
        return [path] if path.exists() else []

    paths: dict[Path, Path] = {}
    for directory in (CORPUS_DIR, transcript_dir()):
        if directory.exists():
            for path in directory.glob("transcript-*.md"):
                paths[path.resolve()] = path
    return sorted(paths.values(), key=lambda item: item.name)


def load_transcript() -> list[Chunk]:
    """Load all clean transcripts and map them to the matching course day."""
    chunks: list[Chunk] = []

    for path in transcript_paths():
        day_code = TRANSCRIPT_DAY_BY_FILE.get(path.name)
        if day_code is None:
            day_match = re.search(r"transcript-0?(\d+)", path.name)
            day_code = _day_code(day_match.group(1)) if day_match else "day01"

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


def _rank(query: str, pool: list[Chunk]) -> list[Chunk]:
    query_terms = terms(query)
    for chunk in pool:
        title_terms = terms(f"{chunk.title} {chunk.doc_id}")
        body_terms = terms(chunk.text)
        chunk.score = len(query_terms & body_terms) + 3 * len(query_terms & title_terms)
    return sorted(pool, key=lambda chunk: (-chunk.score, chunk.page is None, chunk.page or 0))


def _coverage_sample(chunks: list[Chunk], limit: int) -> list[Chunk]:
    if len(chunks) <= limit:
        return list(chunks)
    if limit <= 1:
        return [chunks[0]]
    indexes = {round(index * (len(chunks) - 1) / (limit - 1)) for index in range(limit)}
    return [chunks[index] for index in sorted(indexes)]


def search(query: str, scope_result, chunks: list[Chunk], *, selection: str = "", top_k: int = 6) -> list[Chunk]:
    scope = scope_result.scope

    if scope == "out_of_scope":
        return []

    if scope == "selected_text":
        if not selection.strip():
            return []
        return [Chunk(
            chunk_id="selection", day=scope_result.target_day or "", doc_id="đoạn bôi đen",
            title="Đoạn bạn đang bôi đen", page=scope_result.target_page,
            cite=f"Trang {scope_result.target_page}",
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

    folded_query = fold_text(query)
    is_summary = any(marker in folded_query for marker in SUMMARY_QUERY_MARKERS)

    # Explicit page scope must use that page, even when the question is generic.
    if scope in ("current_page", "ambiguous"):
        return sorted(pool, key=lambda chunk: chunk.doc_id)

    if is_summary and scope == "current_document":
        return sorted(pool, key=lambda chunk: chunk.page or 0)

    if is_summary and scope == "whole_session":
        slides = sorted((c for c in pool if c.kind == "slide"), key=lambda chunk: chunk.page or 0)
        transcripts = sorted((c for c in pool if c.kind == "transcript"), key=lambda chunk: chunk.chunk_id)
        return slides + _coverage_sample(transcripts, 10)

    ordered = _rank(query, pool)
    if not ordered or ordered[0].score == 0:
        return []
    return ordered[:top_k]
