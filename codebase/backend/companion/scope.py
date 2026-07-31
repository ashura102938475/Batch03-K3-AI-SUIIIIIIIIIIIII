"""Quyết định trung tâm của lát cắt: hiểu user đang hỏi ở PHẠM VI nào.

Rule-based, không gọi AI. Ba lý do:
  1. Deterministic -> golden set (CP3) chạy lại ra cùng kết quả, chấm được.
  2. Demo không phụ thuộc quota Gemini ở bước quan trọng nhất.
  3. Sai ở đâu thì chỉ được ra đúng dòng luật, sửa được ngay trong lúc sự kiện.

Evidence từ chatlog: 156/1.261 lượt có nhu cầu summary, 87/156 (55,8%) bị tutor trả
"không tìm thấy / không truy cập được" vì chọn sai phạm vi context để retrieve.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from companion.text import fold_text, has_any

# ----------------------------------------------------------------- intent
SUMMARY_SIGNALS = (
    "tom tat", "tom gon", "tong hop", "summary", "y chinh", "noi dung chinh",
    "noi dung quan trong", "nhung phan chinh", "cac phan chinh", "thao luan chinh",
    "keyword", "tu khoa", "can hoc", "on lai", "ghi chu", "note",
)
EXPLAIN_SIGNALS = ("giai thich", "la gi", "nghia la", "tai sao", "vi sao", "vi du", "khac nhau", "so sanh")
LOGISTICS_SIGNALS = (
    "deadline", "han nop", "nop bai", "nop o dau", "link zoom", "lich hoc", "diem so",
    "tai file", "tai tai lieu", "download", "tai ve", "link repo", "dang ky",
)
OUT_OF_SCOPE_SIGNALS = ("api key", "apikey", "password", "mat khau", "admin", "token he thong", "database", "credential")
EXTERNAL_SUPPORT_SIGNALS = (
    "cai dat pytorch", "pytorch tren macos", "loi cai dat thu vien",
    "sua may tinh", "cau hinh wifi",
)
EXTERNAL_KNOWLEDGE_SIGNALS = (
    "kien thuc ngoai", "nguon ngoai", "nguon ben ngoai", "ben ngoai slide",
    "ngoai slide", "ngoai tai lieu", "tim tren web", "tim tren mang",
    "tra tren web", "internet", "google", "tham khao them", "mo rong them",
) + EXTERNAL_SUPPORT_SIGNALS
PROHIBITED_ASSESSMENT_SIGNALS = (
    "dap an bai kiem tra", "dap an quiz", "chi can dap an", "lam ho bai kiem tra",
    "lam ho bai tap nop", "giai ho bai thi", "tra loi ho bai thi",
)
PROMPT_ATTACK_SIGNALS = (
    "bo qua huong dan", "bo qua moi", "ignore previous", "ignore all", "system prompt",
    "prompt he thong", "ma hoa base64", "base64 toan bo", "dong vai", "quen het luat",
)

# ----------------------------------------------------------------- scope
SESSION_SIGNALS = ("buoi nay", "ca buoi", "toan buoi", "hom nay hoc gi", "buoi hoc nay")
DOCUMENT_SIGNALS = (
    "tai lieu nay", "file nay", "ca file", "ca bai", "toan bo bai", "toan bo slide",
    "tat ca slide", "toan bo tai lieu", "tat ca cac trang", "ca quyen", "toan bo file",
)
PAGE_SIGNALS = ("trang nay", "slide nay", "trang hien tai", "slide hien tai", "o day")
SELECTION_SIGNALS = ("doan nay", "cho nay", "phan nay", "boi den", "doan tren", "doan duoc chon", "doan vua chon")
# Nói "bài này" mà không kèm tín hiệu phạm vi nào -> thật sự mơ hồ, phải hỏi lại.
# Đây là ca có thật trong chatlog: T1164 "tóm tắt cho t tất cả từ trang 1 đến trang 44 bài này học về gì".
AMBIGUOUS_SIGNALS = ("bai nay", "cai nay", "phan tren", "noi dung nay")

DAY_PATTERN = re.compile(r"(?:buoi|day|ngay)\s*0?(\d{1,2})")
PAGE_PATTERN = re.compile(r"(?:trang|slide|page)\s*0?(\d{1,3})")
RANGE_PATTERN = re.compile(r"(?:tu\s*)?(?:trang|slide)\s*0?(\d{1,3})\s*(?:den|-|toi|->)\s*(?:trang|slide)?\s*0?(\d{1,3})")

SCOPE_LABELS = {
    "selected_text": "Đoạn đang bôi đen",
    "current_page": "Trang hiện tại",
    "current_document": "Tài liệu hiện tại",
    "whole_session": "Cả buổi học",
    "external_knowledge": "Kiến thức bổ sung",
    "ambiguous": "Chưa rõ phạm vi",
    "out_of_scope": "Ngoài phạm vi học liệu",
}


@dataclass
class ScopeResult:
    scope: str
    confidence: str          # "cao" | "trung bình" | "thấp"
    reason: str              # hiện thẳng lên UI — HAX G11: giải thích vì sao
    target_day: str | None = None
    target_page: int | None = None
    page_range: tuple[int, int] | None = None

    @property
    def label(self) -> str:
        return SCOPE_LABELS.get(self.scope, self.scope)

    @property
    def needs_clarification(self) -> bool:
        return self.scope == "ambiguous"


def detect_intent(query: str) -> str:
    """prompt_attack > out_of_scope > logistics > summary > explain."""
    folded = fold_text(query)
    if has_any(folded, PROMPT_ATTACK_SIGNALS):
        return "prompt_attack"
    if has_any(folded, OUT_OF_SCOPE_SIGNALS + PROHIBITED_ASSESSMENT_SIGNALS):
        return "out_of_scope"
    if has_any(folded, LOGISTICS_SIGNALS):
        return "logistics"
    if has_any(folded, SUMMARY_SIGNALS):
        return "summary"
    if has_any(folded, EXPLAIN_SIGNALS):
        return "explain"
    return "explain"


def is_prohibited_assessment_request(query: str) -> bool:
    return has_any(fold_text(query), PROHIBITED_ASSESSMENT_SIGNALS)


def wants_external_knowledge(query: str) -> bool:
    return has_any(fold_text(query), EXTERNAL_KNOWLEDGE_SIGNALS)


def detect_scope(query: str, *, has_selection: bool, current_day: str, current_page: int) -> ScopeResult:
    """Trả phạm vi cần đọc + độ tin cậy + lý do.

    Thứ tự kiểm tra có chủ ý: rộng trước, hẹp sau. "tóm tắt tất cả slide" chứa chữ
    "slide" nên nếu kiểm current_page trước sẽ bắt nhầm thành trang hiện tại — đúng
    kiểu lỗi đang thấy trong chatlog.
    """
    folded = fold_text(query)
    intent = detect_intent(query)

    if intent in ("out_of_scope", "logistics", "prompt_attack"):
        return ScopeResult(
            scope="out_of_scope",
            confidence="cao",
            reason={
                "out_of_scope": (
                    "Yêu cầu này là đáp án cho bài được chấm điểm nên Tutor không được làm thay."
                    if is_prohibited_assessment_request(query)
                    else "Câu hỏi không thuộc nội dung học liệu Tutor có thể xác minh."
                ),
                "logistics": "Câu hỏi về logistics khoá học, không nằm trong học liệu.",
                "prompt_attack": "Câu hỏi có dấu hiệu can thiệp hướng dẫn hệ thống.",
            }[intent],
        )

    if wants_external_knowledge(query):
        return ScopeResult(
            scope="external_knowledge",
            confidence="cao",
            reason="Câu hỏi cần kiến thức hoặc nguồn tham khảo ngoài slide nên Tutor sẽ tra cứu nguồn web.",
            target_day=current_day,
            target_page=current_page,
        )

    # ① Cả buổi — "buổi 5", "day 6", "cả buổi này"
    day_match = DAY_PATTERN.search(folded)
    if day_match or has_any(folded, SESSION_SIGNALS):
        day_number = int(day_match.group(1)) if day_match else int(current_day.replace("day", ""))
        target = f"day{day_number:02d}"
        return ScopeResult(
            scope="whole_session",
            confidence="cao" if day_match else "trung bình",
            reason=(
                f"Câu hỏi nhắc tới buổi {day_number} nên đọc toàn bộ tài liệu và transcript của {target}."
                if day_match
                else f"Câu hỏi nhắc 'cả buổi' nên đọc toàn bộ học liệu của {target}."
            ),
            target_day=target,
        )

    # ② Cả tài liệu — "toàn bộ slide", "từ trang 1 đến trang 44"
    range_match = RANGE_PATTERN.search(folded)
    if range_match:
        start, end = sorted((int(range_match.group(1)), int(range_match.group(2))))
        return ScopeResult(
            scope="current_document",
            confidence="cao",
            reason=f"Câu hỏi nêu khoảng trang {start}-{end} nên đọc các trang trong khoảng đó.",
            target_day=current_day,
            page_range=(start, end),
        )
    if has_any(folded, DOCUMENT_SIGNALS):
        return ScopeResult(
            scope="current_document",
            confidence="cao",
            reason="Câu hỏi nhắc tới cả tài liệu/toàn bộ slide nên đọc mọi trang của file đang mở.",
            target_day=current_day,
        )

    # ③ Đoạn bôi đen — user chủ động chọn thì ưu tiên hơn trang
    if has_selection and (has_any(folded, SELECTION_SIGNALS) or not has_any(folded, PAGE_SIGNALS)):
        return ScopeResult(
            scope="selected_text",
            confidence="cao",
            reason="Bạn đang bôi đen một đoạn nên chỉ trả lời trong phạm vi đoạn đó.",
            target_day=current_day,
            target_page=current_page,
        )

    # ④ Một trang cụ thể — "trang này", "trang 37"
    page_match = PAGE_PATTERN.search(folded)
    if page_match:
        page = int(page_match.group(1))
        return ScopeResult(
            scope="current_page",
            confidence="cao",
            reason=f"Câu hỏi chỉ đích danh trang {page}.",
            target_day=current_day,
            target_page=page,
        )
    if has_any(folded, PAGE_SIGNALS):
        return ScopeResult(
            scope="current_page",
            confidence="cao",
            reason=f"Câu hỏi nói 'trang này' nên hiểu là trang {current_page} bạn đang mở.",
            target_day=current_day,
            target_page=current_page,
        )

    # ⑤ Mơ hồ — hỏi lại thay vì đoán liều (HAX G10)
    if has_any(folded, AMBIGUOUS_SIGNALS) or intent == "summary":
        return ScopeResult(
            scope="ambiguous",
            confidence="thấp",
            reason="Câu hỏi chưa nói rõ là trang hiện tại, cả tài liệu, hay cả buổi học.",
            target_day=current_day,
            target_page=current_page,
        )

    return ScopeResult(
        scope="current_page",
        confidence="trung bình",
        reason=f"Không có tín hiệu phạm vi rõ ràng nên mặc định dùng trang {current_page} bạn đang mở.",
        target_day=current_day,
        target_page=current_page,
    )


def detect_scope_llm(
    query: str,
    *,
    has_selection: bool,
    current_day: str,
    current_page: int,
    provider=None,
    fast_model: str | None = None,
) -> ScopeResult:
    """Fast Intent & Scope Classification powered by 1B model tier (e.g., google/gemma-3-1b-it via NVIDIA NIM).

    Falls back gracefully to deterministic rule-based detect_scope when offline or quota exceeded.
    """
    rule_res = detect_scope(query, has_selection=has_selection, current_day=current_day, current_page=current_page)
    if provider is None:
        return rule_res

    target_model = fast_model or os.getenv("NVIDIA_FAST_MODEL", "google/gemma-3-1b-it")
    system_prompt = (
        "Bạn là bộ phân loại Intent & Scope siêu tốc cho VLearn Tutor.\n"
        "Phân tích câu hỏi người học và trả về JSON chuẩn có định dạng:\n"
        '{"intent": "summary"|"explain"|"logistics"|"out_of_scope"|"prompt_attack", '
        '"scope": "selected_text"|"current_page"|"current_document"|"whole_session"|"external_knowledge"|"ambiguous"|"out_of_scope", '
        '"reason": "Giải thích ngắn 1 câu"}'
    )
    user_prompt = f"CÂU HỎI: \"{query}\"\nCONTEXT: Trang hiện tại = {current_page}, Day = {current_day}, Bôi đen = {has_selection}"

    try:
        response = provider.complete(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model=target_model,
            temperature=0.0,
        )
        if response and response.text:
            raw_json = response.text.strip()
            raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json, flags=re.IGNORECASE)
            raw_json = re.sub(r"\s*```$", "", raw_json)
            data = json.loads(raw_json)
            scope = data.get("scope", rule_res.scope)
            if scope in SCOPE_LABELS:
                return ScopeResult(
                    scope=scope,
                    confidence="cao",
                    reason=data.get("reason", rule_res.reason),
                    target_day=rule_res.target_day or current_day,
                    target_page=current_page if scope in ("selected_text", "current_page") else None,
                    page_range=rule_res.page_range if scope == "current_document" else None,
                )
    except Exception:
        pass

    return rule_res
