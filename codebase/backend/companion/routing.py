"""Choose when a learning question should use grounded external knowledge."""
from __future__ import annotations

from companion.text import fold_text, has_any, terms
from companion.scope import is_information_request

# Câu trả lời tự nói "cần chuyển TA" mà nút Chuyển TA lại không bật thì người học đọc
# xong không có gì để bấm. Đây chính là critical failure V3-MISSING-03: câu trả lời ghi
# "cần chuyển cho trợ lý học tập" nhưng ta_handoff_suggested=false.
#
# CỐ Ý KHÔNG dùng lại MISSING_GROUNDING_SIGNALS bên dưới: nó chứa "khong tim thay",
# "khong de cap" — vốn xuất hiện trong những câu trả lời ĐÚNG kiểu "đoạn bôi đen này
# không nói về reinforcement learning" (V3-LOCAL-03), và những ca đó kỳ vọng KHÔNG bật
# TA. Chỉ khớp lời đề nghị chuyển tiếp tường minh.
HANDOFF_TEXT_SIGNALS = (
    "chuyen ta", "chuyen cho ta", "chuyen cho tro ly", "chuyen sang tro ly",
    "tro ly hoc tap", "chuyen cho tro giang", "bam chuyen ta", "lien he tro giang",
    "chuyen cho giang vien",
)

MISSING_GROUNDING_SIGNALS = (
    "thieu du lieu",
    "khong du du lieu",
    "khong co thong tin",
    "khong de cap",
    "khong tim thay",
    "nguon khong du",
    "chua du can cu",
    "cannot answer from",
    "not enough information",
)


def should_try_external(query: str, scope_result, chunks, answer_text: str = "") -> bool:
    """Fallback only for implicit page scope, never for an explicitly requested slide."""
    if scope_result.scope == "external_knowledge":
        return is_information_request(query)
    if scope_result.scope != "current_page" or scope_result.confidence == "cao":
        return False
    if not is_information_request(query):
        return False

    if answer_text and any(signal in fold_text(answer_text) for signal in MISSING_GROUNDING_SIGNALS):
        return True
    if not chunks:
        return True

    query_terms = terms(query)
    if not query_terms:
        return False
    source_terms = terms(" ".join(chunk.text for chunk in chunks))
    overlap = query_terms & source_terms
    # Require >30% of query terms to be covered by internal corpus.
    # A single stray overlap (e.g. "rag" appears once) should not suppress web search.
    overlap_ratio = len(overlap) / len(query_terms)
    return overlap_ratio < 0.3


def should_suggest_ta(
    *,
    scope: str,
    mode: str,
    chunks,
    verified_sources,
    answer_text: str = "",
    external_success: bool = False,
) -> bool:
    """Có bật nút Chuyển TA không? Một nguồn sự thật duy nhất cho mọi call site.

    Trước đây `api.py`, `app.py` và script eval mỗi nơi tự tính một công thức khác nhau,
    nên `--transport direct` và `--transport api` cho kết quả lệch nhau trên cùng một case.
    """
    if scope == "conversation":
        return False
    if answer_text and has_any(fold_text(answer_text), HANDOFF_TEXT_SIGNALS):
        return True
    return bool(
        scope in ("out_of_scope", "ambiguous")
        or (not chunks and not external_success)
        or mode in ("mock", "guardrail")
        or (chunks and not verified_sources)
    )
