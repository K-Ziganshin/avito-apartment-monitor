"""Minimal Telegram Bot API client (send messages, long-poll owner commands)."""

from __future__ import annotations

import logging
from typing import Any

import requests

log = logging.getLogger(__name__)


class Telegram:
    def __init__(self, token: str, chat_id: str, session: requests.Session | None = None) -> None:
        self._base = f"https://api.telegram.org/bot{token}"
        self.chat_id = str(chat_id)
        self._http = session or requests.Session()
        self._offset = 0

    def send(self, text: str) -> bool:
        try:
            self._http.post(
                f"{self._base}/sendMessage", json={"chat_id": self.chat_id, "text": text}, timeout=15
            ).raise_for_status()
        except requests.RequestException as exc:
            log.warning("Telegram send failed: %s", type(exc).__name__)  # never log the URL: it contains the token
            return False
        return True

    def owner_commands(self, timeout: int = 30) -> list[str]:
        """Long-poll updates and return text commands from the owner's chat only."""
        resp = self._http.get(
            f"{self._base}/getUpdates", params={"offset": self._offset + 1, "timeout": timeout}, timeout=timeout + 10
        )
        resp.raise_for_status()
        return self.owner_texts(resp.json().get("result", []))

    def owner_texts(self, updates: list[dict[str, Any]]) -> list[str]:
        texts = []
        for update in updates:
            self._offset = max(self._offset, update.get("update_id", 0))
            message = update.get("message") or {}
            if str(message.get("chat", {}).get("id")) == self.chat_id and message.get("text"):
                texts.append(message["text"].strip().lower())
        return texts
