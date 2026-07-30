from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from providers.base import Provider, ToolCall
from tools import TOOL_FUNCTIONS
from tools._shared import fold_text


@dataclass
class AgentRun:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


def _explicit_parallel_source_tools(user_messages: list[dict[str, str]]) -> set[str]:
    if len(user_messages) != 1:
        return set()

    content = user_messages[0].get("content", "")
    if content.startswith("Conversation context for a multi-turn eval."):
        return set()

    text = fold_text(content)
    requests_web = any(marker in text for marker in (" tren web", "web ", "tin tuc", " news"))
    requests_social = any(marker in text for marker in ("tweet", "twitter", "mang xa hoi", " social"))
    if requests_web and requests_social:
        return {"lookup", "social_search"}
    return set()


class ResearchAgent:
    def __init__(
        self,
        provider: Provider,
        *,
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model

    def run(self, user_messages: list[dict[str, str]], *, tool_choice: Any | None = None) -> AgentRun:
        messages = [{"role": "system", "content": self.system_prompt}, *user_messages]
        response = self.provider.complete(
            messages,
            self.tools,
            model=self.model,
            temperature=0.0,
            tool_choice=tool_choice,
        )
        required_source_tools = _explicit_parallel_source_tools(user_messages)
        for _ in range(2):
            actual_tools = {call.name for call in response.tool_calls}
            missing_tools = required_source_tools - actual_tools
            if not missing_tools:
                break
            retry_messages = [
                {
                    "role": "system",
                    "content": (
                        f"{self.system_prompt}\n\n"
                        "Tool-call validation: the request explicitly names multiple independent sources. "
                        f"Return a fresh response containing one call for every source; missing tools: "
                        f"{', '.join(sorted(missing_tools))}."
                    ),
                },
                *user_messages,
            ]
            response = self.provider.complete(
                retry_messages,
                self.tools,
                model=self.model,
                temperature=0.0,
                tool_choice=tool_choice,
            )
        results: list[dict[str, Any]] = []
        for call in response.tool_calls:
            func = TOOL_FUNCTIONS.get(call.name)
            if not func:
                results.append({"tool": call.name, "error": "unknown_tool"})
                continue
            try:
                result = func(**call.args)
            except Exception as exc:  # keep eval robust; failures are evidence
                result = {"error": type(exc).__name__, "message": str(exc)}
            results.append({"tool": call.name, "args": call.args, "result": result})
        return AgentRun(text=response.text, tool_calls=response.tool_calls, tool_results=results)
