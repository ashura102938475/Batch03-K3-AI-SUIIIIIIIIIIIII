from __future__ import annotations

import json
import os
import time
import urllib.parse
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
    """Send push notification to Telegram TA Bot / Webhook channel.

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
    log_entry = json.dumps(payload, ensure_ascii=False)
    with ESCALATIONS_LOG.open(mode="a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

    pushed = False
    delivery_status_parts: list[str] = ["logged_locally"]

    # 2. Check for Telegram Bot Config
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if bot_token and chat_id:
        tg_text = (
            "🚨 *YÊU CẦU HỖ TRỢ TA MỚI*\n\n"
            f"⏰ *Thời gian*: `{timestamp}`\n"
            f"📌 *Lý do*: `{reason}`\n"
            f"📍 *Phạm vi*: `{current_day}` (Trang {current_page})\n"
            f"💬 *Câu hỏi*: \"{student_query}\"\n\n"
            "👉 _VLearn Smart Contextual Companion_"
        )
        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        tg_payload = {
            "chat_id": chat_id,
            "text": tg_text,
            "parse_mode": "Markdown",
        }

        try:
            req = urllib.request.Request(
                tg_url,
                data=json.dumps(tg_payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "VLearn-Companion-TelegramNotifier/1.0"},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    pushed = True
                    delivery_status_parts.append("pushed_to_telegram")
        except Exception as exc:
            delivery_status_parts.append(f"telegram_error: {exc}")

    # 3. Check for Webhook URL (Discord / Slack / Generic Webhook)
    webhook_url = os.getenv("TA_WEBHOOK_URL", "").strip()
    if webhook_url:
        webhook_body = {
            "content": f"🚨 **Yêu cầu hỗ trợ TA mới!**\n- **Thời gian**: `{timestamp}`\n- **Lý do**: `{reason}`\n- **Phạm vi**: `{current_day}` (Trang {current_page})\n- **Câu hỏi**: *\"{student_query}\"*",
        }
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(webhook_body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    pushed = True
                    delivery_status_parts.append("pushed_to_webhook")
        except Exception as exc:
            delivery_status_parts.append(f"webhook_error: {exc}")

    delivery_status = ", ".join(delivery_status_parts)
    return {
        "status": "escalated",
        "pushed": pushed,
        "delivery_status": delivery_status,
        "payload": payload,
        "message": f"Đã ghi nhận yêu cầu chuyển TA ({delivery_status}).",
    }
