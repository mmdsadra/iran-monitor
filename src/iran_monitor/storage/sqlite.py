import json
import sqlite3

from iran_monitor.models.news import NewsItem


class SQLiteStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""
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
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_published_at
                ON news(published_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_source
                ON news(source_type, source_name)
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS source_state (
                    source_name TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    last_message_id INTEGER,
                    last_collected_at TEXT
                )
            """)

    def save(self, item: NewsItem) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
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
                    item.published_at.isoformat()
                    if item.published_at
                    else None,
                    item.content_hash,
                    json.dumps(
                        item.raw_data,
                        ensure_ascii=False,
                    ),
                ),
            )

            return cursor.rowcount == 1

    def save_many(self, items: list[NewsItem]) -> int:
        inserted = 0

        for item in items:
            if self.save(item):
                inserted += 1

        return inserted

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM news"
            ).fetchone()

            return row[0]

    def get_last_message_id(
        self,
        source_name: str,
    ) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT last_message_id
                FROM source_state
                WHERE source_name = ?
                """,
                (source_name,),
            ).fetchone()

            return row[0] if row else None

    def update_source_state(
        self,
        source_name: str,
        source_type: str,
        last_message_id: int | None,
    ):
        from datetime import datetime, timezone

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO source_state (
                    source_name,
                    source_type,
                    last_message_id,
                    last_collected_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source_name)
                DO UPDATE SET
                    last_message_id = excluded.last_message_id,
                    last_collected_at = excluded.last_collected_at
                """,
                (
                    source_name,
                    source_type,
                    last_message_id,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            
    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        pass

