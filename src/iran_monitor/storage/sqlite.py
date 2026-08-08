from __future__ import annotations

import sqlite3
from pathlib import Path

from iran_monitor.models.news import NewsItem


class SQLiteStorage:
    """Persistent storage for collected news items."""

    def __init__(self, db_path: str | Path = "data/iran_monitor.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row

        self._initialize()

    def _initialize(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                language TEXT,
                title TEXT,
                text TEXT NOT NULL,
                url TEXT,
                published_at TEXT,
                content_hash TEXT NOT NULL UNIQUE,
                raw_data TEXT
            )
            """
        )

        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_news_published_at
            ON news(published_at)
            """
        )

        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_news_source
            ON news(source_type, source_name)
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS source_state (
                source_name TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                last_message_id INTEGER,
                last_collected_at TEXT
            )
            """
        )
        self.connection.commit()

    def save(self, item: NewsItem) -> bool:
        """Save one item. Returns False if it already exists."""

        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO news (
                id,
                source_name,
                source_type,
                language,
                title,
                text,
                url,
                published_at,
                content_hash,
                raw_data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.source_name,
                item.source_type,
                item.language,
                item.title,
                item.text,
                item.url,
                (
                    item.published_at.isoformat()
                    if item.published_at
                    else None
                ),
                item.content_hash,
                (
                    str(item.raw_data)
                    if item.raw_data
                    else None
                ),
            ),
        )

        self.connection.commit()

        return cursor.rowcount > 0

    def save_many(self, items: list[NewsItem]) -> int:
        inserted = 0

        for item in items:
            if self.save(item):
                inserted += 1

        return inserted

    def count(self) -> int:
        cursor = self.connection.execute(
            "SELECT COUNT(*) FROM news"
        )

        return int(cursor.fetchone()[0])

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SQLiteStorage":
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    def get_last_message_id(
        self,
        source_name: str,
    ) -> int | None:
        cursor = self.connection.execute(
            """
            SELECT last_message_id
            FROM source_state
            WHERE source_name = ?
            """,
            (source_name,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return row["last_message_id"]


    def update_source_state(
        self,
        *,
        source_name: str,
        source_type: str,
        last_message_id: int,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO source_state (
                source_name,
                source_type,
                last_message_id,
                last_collected_at
            )
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(source_name)
            DO UPDATE SET
                last_message_id = excluded.last_message_id,
                last_collected_at = excluded.last_collected_at
            """,
            (
                source_name,
                source_type,
                last_message_id,
            ),
        )

        self.connection.commit()