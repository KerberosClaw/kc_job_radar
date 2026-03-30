"""Telegram notification for kc_job_radar."""

from pathlib import Path

import httpx

from .config import TelegramConfig

BASE_URL = "https://api.telegram.org/bot{token}"


def send_telegram(config: TelegramConfig, message: str) -> bool:
    """Send a text message via Telegram Bot API."""
    try:
        resp = httpx.post(
            f"{BASE_URL.format(token=config.bot_token)}/sendMessage",
            json={
                "chat_id": config.chat_id,
                "text": message,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def send_document(config: TelegramConfig, file_path: str, caption: str = "") -> bool:
    """Send a file via Telegram Bot API."""
    try:
        path = Path(file_path)
        if not path.exists():
            return False
        with path.open("rb") as f:
            resp = httpx.post(
                f"{BASE_URL.format(token=config.bot_token)}/sendDocument",
                data={
                    "chat_id": config.chat_id,
                    "caption": caption,
                },
                files={"document": (path.name, f)},
                timeout=30,
            )
        return resp.status_code == 200
    except Exception:
        return False
