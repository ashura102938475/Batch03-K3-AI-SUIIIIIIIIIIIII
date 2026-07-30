from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class EmptyResponseError(RuntimeError):
    """Provider trả response không có `choices`.

    OpenRouter trả body kiểu này khi upstream quá tải hoặc bị lọc nội dung. Đây là
    lỗi tạm thời nên retry được — nếu để nguyên, `resp.choices[0]` ném TypeError
    khó hiểu và `run_eval.py` ghi thành provider_error làm hỏng cả run.
    """


def is_rate_limit(exc: Exception) -> bool:
    text = str(exc)
    return getattr(exc, "code", None) == 429 or "429" in text or "RESOURCE_EXHAUSTED" in text


def is_daily_quota(exc: Exception) -> bool:
    """Hạn mức theo NGÀY đã cạn — retry bao nhiêu lần cũng vô ích.

    Free tier của Gemini trả quotaId `GenerateRequestsPerDayPerProjectPerModel`
    kèm `retryDelay` vài chục giây, nhưng delay đó gây hiểu nhầm: quota chỉ reset
    vào đầu ngày. Phải bỏ cuộc ngay để `run_eval.py` ghi provider_error và dừng,
    thay vì ngồi sleep hàng chục phút.
    """
    text = str(exc)
    return "PerDay" in text or "per day" in text.lower()


def server_retry_delay(exc: Exception) -> float | None:
    match = re.search(r"(?:'retryDelay':\s*'|retry in )(\d+(?:\.\d+)?)s", str(exc))
    return float(match.group(1)) if match else None


class RequestPacer:
    """Giãn cách request và lùi dần khi bị rate limit theo phút.

    run_eval.py biến mọi exception thành failure_type="provider_error", và một run
    chỉ dùng được để report khi provider_error_cases == 0 — nên đáng để chờ ở lỗi
    tạm thời, nhưng phải thoát ngay ở lỗi hết hạn mức ngày.
    """

    def __init__(self, *, interval_env: str, retries_env: str, default_interval: float = 0.0) -> None:
        self.min_interval = float(os.getenv(interval_env, str(default_interval)))
        self.max_retries = int(os.getenv(retries_env, "5"))
        self._last_at = 0.0

    def run(self, call: Callable[[], Any]) -> Any:
        delay = max(self.min_interval, 2.0)
        for attempt in range(self.max_retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last_at)
            if wait > 0:
                time.sleep(wait)
            try:
                self._last_at = time.monotonic()
                return call()
            except Exception as exc:
                if is_daily_quota(exc):
                    raise RuntimeError(
                        f"Hết hạn mức theo NGÀY của provider, chờ không giải quyết được. Gốc: {exc}"
                    ) from exc
                retryable = is_rate_limit(exc) or isinstance(exc, EmptyResponseError)
                if not retryable or attempt == self.max_retries:
                    raise
                time.sleep(server_retry_delay(exc) or delay)
                delay = min(delay * 2, 60.0)
        raise RuntimeError("unreachable")


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass
class ModelResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any | None = None


class Provider(Protocol):
    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        """Return normalized text/tool calls regardless of vendor API shape."""
