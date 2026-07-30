from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .vlearn.tool import detect_scope_tool, search_corpus_tool, escalate_ta_tool


TOOL_FUNCTIONS = {
    "detect_scope": detect_scope_tool,
    "search_corpus": search_corpus_tool,
    "escalate_ta": escalate_ta_tool,
}


def load_tool_declarations(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["tools"]


def to_openai_tools(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": item["name"],
            "description": item.get("description", ""),
            "parameters": item.get("parameters", {"type": "object", "properties": {}}),
        },
    } for item in declarations]
