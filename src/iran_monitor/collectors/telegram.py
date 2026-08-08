from __future__ import annotations

import hashlib
from datetime import timezone

from telethon import TelegramClient

from iran_monitor.collectors.base import BaseCollector
from iran_monitor.models.news import NewsItem


class TelegramCollector(BaseCollector):
    """Collect messages from a Telegram channel."""

    def __init__(
        self,
        client: TelegramClient,
        *,
        source_name: str,
        username: str,
        language: str,
        limit: int = 100,
    ):
        self.client = client
        self.source_name = source_name
        self.username = username
        self.language = language
        self.limit = limit

    async def collect(
        self,
        *,
        min_id: int = 0,
    ) -> list[NewsItem]:
        items: list[NewsItem] = []

        async for message in self.client.iter_messages(
            self.username,
            limit=self.limit,
            min_id=min_id,
            reverse=True,
        ):
            # Defensive check: never process an old message.
            if message.id <= min_id:
                continue

            if not message.message:
                continue

            text = message.message.strip()

            published_at = None

            if message.date:
                published_at = message.date.astimezone(
                    timezone.utc
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
    
    async def get_latest_message_id(self) -> int | None:
        message = await self.client.get_messages(
            self.username,
            limit=1,
        )

        if not message:
            return None

        return message[0].id