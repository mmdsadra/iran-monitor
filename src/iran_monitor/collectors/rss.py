from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from iran_monitor.config.models import RSSSource
from iran_monitor.models.news import NewsItem


class RSSCollector:
    """Collect and normalize news items from an RSS feed."""

    def __init__(self, source: RSSSource):
        self.source = source

    def collect(self) -> list[NewsItem]:
        """Fetch the RSS feed and return normalized NewsItem objects."""
        if not self.source.enabled:
            return []

        feed = feedparser.parse(self.source.url)

        if feed.bozo and not feed.entries:
            raise RuntimeError(
                f"Failed to parse RSS feed: {self.source.url}"
            )

        items: list[NewsItem] = []

        for entry in feed.entries:
            title = self._get_title(entry)
            text = self._get_text(entry)
            url = self._get_url(entry)
            published_at = self._get_published_at(entry)

            if not text:
                continue

            content_hash = self._make_hash(
                title=title,
                text=text,
                url=url,
            )

            item = NewsItem(
                id=content_hash,
                source_name=self.source.name,
                source_type="rss",
                language=self.source.language,
                title=title,
                text=text,
                url=url,
                published_at=published_at,
                content_hash=content_hash,
                raw_data=dict(entry),
            )

            items.append(item)

        return items

    @staticmethod
    def _get_title(entry) -> str | None:
        title = entry.get("title")
        return title.strip() if title else None

    @staticmethod
    def _get_text(entry) -> str:
        text = (
            entry.get("summary")
            or entry.get("description")
            or entry.get("title")
            or ""
        )

        return text.strip()

    @staticmethod
    def _get_url(entry) -> str | None:
        url = entry.get("link")
        return url.strip() if url else None

    @staticmethod
    def _get_published_at(entry) -> datetime | None:
        raw_date = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("created")
        )

        if not raw_date:
            return None

        try:
            return parsedate_to_datetime(raw_date).astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _make_hash(
        *,
        title: str | None,
        text: str,
        url: str | None,
    ) -> str:
        raw = "|".join(
            [
                title or "",
                text,
                url or "",
            ]
        )

        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
