from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone

from telethon import TelegramClient

from iran_monitor.collectors.base import BaseCollector
from iran_monitor.models.news import NewsItem


class TelegramCollector(BaseCollector):
    """Collect messages from a Telegram channel."""

    def __init__(
        self,
        *,
        source_name: str,
        username: str,
        language: str,
    ):
        self.source_name = source_name
        self.username = username
        self.language = language

        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        session_path = os.getenv(
            "TELEGRAM_SESSION_PATH",
            "telegram_sessions/iran_monitor",
        )

        if not api_id or not api_hash:
            raise RuntimeError(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH "
                "must be set in the environment."
            )

        self.client = TelegramClient(
            session_path,
            int(api_id),
            api_hash,
        )

    async def collect(self) -> list[NewsItem]:
        """Collect recent messages from the configured channel."""

        items: list[NewsItem] = []

        async with self.client:
            async for message in self.client.iter_messages(
                self.username,
                limit=100,
            ):
                if not message.message:
                    continue

                text = message.message.strip()

                published_at = (
                    message.date.astimezone(timezone.utc)
                    if message.date
                    else None
                )

                message_url = self._build_message_url(
                    message.id
                )

                content_hash = self._make_hash(
                    text=text,
                    message_id=message.id,
                )

                items.append(
                    NewsItem(
                        id=content_hash,
                        source_name=self.source_name,
                        source_type="telegram",
                        language=self.language,
                        title=None,
                        text=text,
                        url=message_url,
                        published_at=published_at,
                        content_hash=content_hash,
                        raw_data={
                            "message_id": message.id,
                        },
                    )
                )

        return items

    def _build_message_url(
        self,
        message_id: int,
    ) -> str:
        username = self.username.lstrip("@")
        return f"https://t.me/{username}/{message_id}"

    @staticmethod
    def _make_hash(
        *,
        text: str,
        message_id: int,
    ) -> str:
        raw = f"{message_id}|{text}"
        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()
