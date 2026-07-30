from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ESCALATIONS_LOG = ROOT / "runs" / "ta_escalations.jsonl"


def notify_ta_channel(
    reason: str,
    student_query: str,
    current_day: str = "day01",
    current_page: int = 1,
    turn_id: str | None = None,
) -> dict[str, Any]:
    """Send push notification to TA Channel via Webhook (Discord / Slack / Telegram / Custom HTTP Webhook).

    Also logs the escalation locally to `runs/ta_escalations.jsonl`.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "event": "ta_escalation",
        "timestamp": timestamp,
        "reason": reason,
        "student_query": student_query,
        "current_day": current_day,
        "current_page": current_page,
        "turn_id": turn_id or f"turn_{int(time.time())}",
    }

    # 1. Always append to local escalations log file
    ESCALATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ESCALATION_LOG_OPEN(ESCALATIONS_LOG):
        pass

    log_entry = json.dumps(payload, ensure_ascii=False)
    with ESCALATIONS_LOG.open(mode="a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

    # 2. Check for configured TA Webhook URL
    webhook_url = os.getenv("TA_WEBHOOK_URL", "").strip()
    pushed = False
    delivery_status = "logged_locally"

    if webhook_url:
        # Format payload for Discord / Slack / Standard HTTP Webhooks
        webhook_body = {
            "content": f"🚨 **Yêu cầu hỗ trợ TA mới!**\n- **Thời gian**: `{timestamp}`\n- **Lý do**: `{reason}`\n- **Phạm vi**: `{current_day}` (Trang {current_page})\n- **Câu hỏi**: *\"{student_query}\"*",
            "embeds": [
                {
                    "title": "VLearn Smart Companion — TA Escalation",
                    "color": 15158332,  # Red alert
                    "fields": [
                        {"name": "Lý do", "value": reason, "inline": True},
                        {"name": "Phạm vi", "value": f"{current_day} (Trang {current_page})", "inline": True},
                        {"name": "Nội dung câu hỏi", "value": student_query},
                    ],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            ],
        }

        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(webhook_body).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "VLearn-Companion-Notifier/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    pushed = True
                    delivery_status = "pushed_to_webhook"
        except Exception as exc:
            delivery_status = f"webhook_error: {exc}"

    return {
        "status": "escalated",
        "pushed": pushed,
        "delivery_status": delivery_status,
        "payload": payload,
        "message": f"Đã ghi nhận yêu cầu chuyển TA ({delivery_status}).",
    }


def ESCALATION_LOG_OPEN(path: Path):
    """Context helper to ensure directory exists."""
    class DummyContext:
        def __enter__(self): return None
        def __exit__(self, *args): pass
    return DummyContext()
