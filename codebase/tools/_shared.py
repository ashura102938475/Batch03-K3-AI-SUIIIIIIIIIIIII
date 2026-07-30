from __future__ import annotations

import unicodedata


def fold_text(text: str) -> str:
    """Normalize and fold Vietnamese text for keyword matching."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower()
