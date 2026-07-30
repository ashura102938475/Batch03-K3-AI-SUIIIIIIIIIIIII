"""Chuẩn hoá tiếng Việt để so khớp keyword ổn định.

Phỏng theo `tools/_shared.py` của Day04 Lab, sửa một chỗ: bản gốc dùng NFD rồi bỏ
combining mark nên `ư`/`ơ`/dấu thanh về đúng chữ cái, nhưng `đ` (U+0111) không phân
rã được — `được` thành `đuoc`, rồi regex `[a-z0-9]+` cắt mất thành `uoc`. Thêm một
bước map `đ -> d` cho sạch.
"""
from __future__ import annotations

import re
import unicodedata

# Từ quá phổ biến trong câu hỏi tiếng Việt, giữ lại chỉ làm nhiễu điểm số.
STOPWORDS = {
    "ban", "bao", "cac", "cai", "can", "cho", "co", "cua", "duoc", "gi", "giup",
    "la", "lam", "minh", "mot", "nay", "nen", "nhung", "the", "thi", "toi",
    "trong", "va", "ve", "voi", "and", "for", "the", "with",
}


def fold_text(text: str) -> str:
    """`Tóm tắt Đoạn Này` -> `tom tat doan nay`."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.replace("đ", "d")


def terms(text: str) -> set[str]:
    folded = fold_text(text)
    return {t for t in re.findall(r"[a-z0-9]+", folded) if len(t) > 1 and t not in STOPWORDS}


def has_any(folded_query: str, phrases: tuple[str, ...]) -> bool:
    """Khớp cụm từ trên chuỗi ĐÃ fold. Cụm truyền vào cũng phải không dấu."""
    return any(phrase in folded_query for phrase in phrases)
