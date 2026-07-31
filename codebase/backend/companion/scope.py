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

from companion.text import fold_text, has_any, terms

# ----------------------------------------------------------------- intent
SUMMARY_SIGNALS = (
    "tom tat", "tom gon", "tom lai", "tong hop", "summary", "recap", "sum up",
    "y chinh", "noi dung chinh",
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
# Nói thẳng là muốn ra khỏi học liệu -> luôn tính là cần nguồn ngoài.
EXTERNAL_STRONG_SIGNALS = (
    "kien thuc ngoai", "nguon ngoai", "nguon ben ngoai", "tim tren web",
    "tim tren mang", "tra tren web", "internet", "google",
) + EXTERNAL_SUPPORT_SIGNALS
# Mơ hồ: "ngoài slide" có thể là "ngoài internet" mà cũng có thể là "thầy nói thêm
# ngoài slide" — tức chính transcript của buổi học, vốn NẰM TRONG học liệu.
EXTERNAL_WEAK_SIGNALS = (
    "ben ngoai slide", "ngoai slide", "ngoai tai lieu", "tham khao them", "mo rong them",
)
# Có mặt những cụm này thì "ngoài slide" đang trỏ vào lời giảng, không phải web.
LECTURE_CONTEXT_SIGNALS = (
    "thay noi", "thay giang", "thay co noi", "thay day", "giang vien noi", "giang vien giang",
    "co noi", "trong buoi", "buoi hoc", "transcript", "ghi am", "bai giang", "thay nhac",
)
EXTERNAL_KNOWLEDGE_SIGNALS = EXTERNAL_STRONG_SIGNALS + EXTERNAL_WEAK_SIGNALS
PROHIBITED_ASSESSMENT_SIGNALS = (
    "dap an bai kiem tra", "dap an quiz", "chi can dap an", "lam ho bai kiem tra",
    "lam ho bai tap nop", "giai ho bai thi", "tra loi ho bai thi",
)
PROMPT_ATTACK_SIGNALS = (
    "bo qua huong dan", "bo qua moi", "ignore previous", "ignore all", "system prompt",
    "prompt he thong", "ma hoa base64", "base64 toan bo", "dong vai", "quen het luat",
)
CONVERSATION_PHRASES = {
    "hello", "hi", "hey", "hi there", "hello there",
    "xin chao", "chao", "chao ban", "chao tutor", "hello tutor", "hello bot",
    "cam on", "cam on ban", "thanks", "thank you", "ok", "okay",
}
INFORMATION_REQUEST_SIGNALS = (
    "la gi", "tai sao", "vi sao", "nhu the nao", "the nao", "bao nhieu", "o dau",
    "giai thich", "tom tat", "tong hop", "so sanh", "phan tich", "cho biet",
    "huong dan", "tim", "tra cuu", "dinh nghia", "vai tro", "tam quan trong", "cach ",
    "what", "why", "how", "when", "where", "which", "explain", "summarize",
    "compare", "define", "show me", "tell me", "find ",
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

# "đọc hết bộ slide này" chứa nguyên cụm "slide nay" nên nhánh ④ cướp mất thành
# current_page — đúng lỗi mà docstring của detect_scope cảnh báo nhưng chưa chặn.
# Đây là luật cấu trúc (tín hiệu độ rộng đè tín hiệu trang), không phải nhồi từ khoá.
BREADTH_MARKERS = ("het ", "toan bo", "tat ca", "ca bo", "full", "all ", "moi trang", "tu dau den cuoi")

# Danh từ neo phạm vi: có mặt thì câu hỏi ít nhất đã trỏ vào MỘT loại tài liệu nào đó.
SCOPE_ANCHOR_NOUNS = (
    "slide", "deck", "tai lieu", "file", "trang", "page", "bai", "buoi",
    "lesson", "session", "chuong", "document", "transcript", "doan",
)

DAY_PATTERN = re.compile(r"(?:buoi|day|ngay)\s*0?(\d{1,2})")
PAGE_PATTERN = re.compile(r"(?:trang|slide|page)\s*0?(\d{1,3})")
RANGE_PATTERN = re.compile(r"(?:tu\s*)?(?:trang|slide)\s*0?(\d{1,3})\s*(?:den|-|toi|->)\s*(?:trang|slide)?\s*0?(\d{1,3})")

SCOPE_LABELS = {
    "conversation": "Hội thoại",
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
    # Luật có thực sự khớp một tín hiệu, hay đã bó tay rồi đoán? Đây là thứ cho phép
    # classifier lai (companion/classify.py) chỉ hỏi LLM ở đúng ca luật không quyết được,
    # nhờ vậy model dở hay chết cũng không kéo đổ các ca luật vốn đã đúng.
    origin: str = "rule"     # rule | fallthrough | llm | safety | forced

    @property
    def label(self) -> str:
        return SCOPE_LABELS.get(self.scope, self.scope)

    @property
    def needs_clarification(self) -> bool:
        return self.scope == "ambiguous"


# Đuôi xưng hô có thể gắn sau một lời chào mà không đổi nghĩa.
GREETING_SUFFIXES = ("ban", "tutor", "bot", "ai", "moi nguoi", "ad", "shop", "nhe", "a", "ah", "ak")


def is_conversation(query: str) -> bool:
    """Khớp lời chào, chịu được đuôi xưng hô.

    Danh sách khớp-chính-xác cũ có "xin chao" và "chao ban" nhưng thiếu "xin chao ban",
    nên lời chào phổ biến nhất lại rơi xuống nhánh mơ hồ và hiện nút Chuyển TA.
    """
    normalized = re.sub(r"[^a-z0-9\s]", " ", fold_text(query))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized in CONVERSATION_PHRASES:
        return True
    for suffix in GREETING_SUFFIXES:
        if normalized.endswith(" " + suffix):
            trimmed = normalized[: -(len(suffix) + 1)].strip()
            if trimmed in CONVERSATION_PHRASES:
                return True
    return False


def is_information_request(query: str) -> bool:
    folded = fold_text(query)
    return "?" in query or has_any(folded, INFORMATION_REQUEST_SIGNALS)


def detect_intent(query: str) -> str:
    """prompt_attack > out_of_scope > logistics > conversation > summary > explain."""
    folded = fold_text(query)
    if has_any(folded, PROMPT_ATTACK_SIGNALS):
        return "prompt_attack"
    if has_any(folded, OUT_OF_SCOPE_SIGNALS + PROHIBITED_ASSESSMENT_SIGNALS):
        return "out_of_scope"
    if has_any(folded, LOGISTICS_SIGNALS):
        return "logistics"
    if is_conversation(query):
        return "conversation"
    if has_any(folded, SUMMARY_SIGNALS):
        return "summary"
    if has_any(folded, EXPLAIN_SIGNALS):
        return "explain"
    return "explain"


def is_prohibited_assessment_request(query: str) -> bool:
    return has_any(fold_text(query), PROHIBITED_ASSESSMENT_SIGNALS)


def wants_external_knowledge(query: str) -> bool:
    """Có thật sự muốn ra khỏi học liệu không?

    Tín hiệu yếu ("ngoài slide") bị vô hiệu khi câu đang nói tới lời giảng hoặc chỉ đích
    danh một buổi học: "thầy nói thêm ngoài slide ở buổi 2" là yêu cầu đọc transcript —
    thứ NẰM TRONG học liệu — chứ không phải yêu cầu tra web.
    """
    folded = fold_text(query)
    if has_any(folded, EXTERNAL_STRONG_SIGNALS):
        return True
    if not has_any(folded, EXTERNAL_WEAK_SIGNALS):
        return False
    return not (has_any(folded, LECTURE_CONTEXT_SIGNALS) or DAY_PATTERN.search(folded))


def is_floor_ambiguous(query: str) -> bool:
    """Sàn mơ hồ tất định — câu quá ngắn và không trỏ vào phạm vi nào.

    Là chốt chặn đứng TRÊN cả LLM: "recap giúp" thì dù model có tự tin đoán trang
    hiện tại, hỏi lại vẫn đúng hơn đoán liều (HAX G10). Nhờ vậy việc bật classifier
    không biến hệ thống thành máy đoán bừa.
    """
    folded = fold_text(query)
    if has_any(folded, AMBIGUOUS_SIGNALS):
        return True
    if has_any(folded, SCOPE_ANCHOR_NOUNS):
        return False
    if DAY_PATTERN.search(folded) or PAGE_PATTERN.search(folded):
        return False
    return len(terms(query)) <= 4


def detect_scope(query: str, *, has_selection: bool, current_day: str, current_page: int) -> ScopeResult:
    """Trả phạm vi cần đọc + độ tin cậy + lý do.

    Thứ tự kiểm tra có chủ ý: rộng trước, hẹp sau. "tóm tắt tất cả slide" chứa chữ
    "slide" nên nếu kiểm current_page trước sẽ bắt nhầm thành trang hiện tại — đúng
    kiểu lỗi đang thấy trong chatlog.
    """
    folded = fold_text(query)
    intent = detect_intent(query)

    if intent == "conversation":
        return ScopeResult(
            scope="conversation",
            confidence="cao",
            reason="Đây là lời chào hoặc phản hồi xã giao, không phải yêu cầu tra cứu kiến thức.",
        )

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

    if wants_external_knowledge(query) and is_information_request(query):
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
    # "đọc hết bộ slide này" có 'slide nay' nhưng ý là cả tệp — tín hiệu độ rộng
    # phải đè tín hiệu trang, nếu không sẽ tóm tắt đúng một trang rồi báo xong.
    if has_any(folded, PAGE_SIGNALS) and not has_any(folded, BREADTH_MARKERS):
        return ScopeResult(
            scope="current_page",
            confidence="cao",
            reason=f"Câu hỏi nói 'trang này' nên hiểu là trang {current_page} bạn đang mở.",
            target_day=current_day,
            target_page=current_page,
        )

    # ⑤ Mơ hồ — hỏi lại thay vì đoán liều (HAX G10).
    # Cổng `not is_information_request` nằm ở ĐÂY chứ không phải đầu hàm: đặt trước
    # nhánh ①-④ thì "Tạo 3 câu hỏi ôn tập dựa trên slide trang 3" (một mệnh lệnh,
    # không phải câu hỏi) bị nuốt thành ambiguous dù đã chỉ đích danh trang.
    if has_any(folded, AMBIGUOUS_SIGNALS):
        return ScopeResult(
            scope="ambiguous",
            confidence="thấp",
            reason="Câu hỏi chưa nói rõ là trang hiện tại, cả tài liệu, hay cả buổi học.",
            target_day=current_day,
            target_page=current_page,
            origin="rule",
        )
    if intent == "explain" and not is_information_request(query):
        return ScopeResult(
            scope="ambiguous",
            confidence="thấp",
            reason="Tin nhắn chưa thể hiện một câu hỏi hoặc yêu cầu kiến thức cụ thể.",
            target_day=current_day,
            target_page=current_page,
            origin="fallthrough",
        )
    if intent == "summary":
        return ScopeResult(
            scope="ambiguous",
            confidence="thấp",
            reason="Câu hỏi chưa nói rõ là trang hiện tại, cả tài liệu, hay cả buổi học.",
            target_day=current_day,
            target_page=current_page,
            origin="fallthrough",
        )

    return ScopeResult(
        scope="current_page",
        confidence="trung bình",
        reason=f"Không có tín hiệu phạm vi rõ ràng nên mặc định dùng trang {current_page} bạn đang mở.",
        target_day=current_day,
        target_page=current_page,
        origin="fallthrough",
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
        '{"intent": "conversation"|"summary"|"explain"|"logistics"|"out_of_scope"|"prompt_attack", '
        '"scope": "conversation"|"selected_text"|"current_page"|"current_document"|"whole_session"|"external_knowledge"|"ambiguous"|"out_of_scope", '
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
