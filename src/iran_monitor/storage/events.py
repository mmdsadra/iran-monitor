import json
import sqlite3

from iran_monitor.events.model import Event, EventEntity
from iran_monitor.intelligence.evidence import Evidence


class EventRepository:
    """SQLite persistence for normalized events and their evidence."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT NOT NULL,
                    location_text TEXT,
                    country TEXT,
                    city TEXT,
                    latitude REAL,
                    longitude REAL,
                    occurred_at TEXT,
                    severity REAL NOT NULL,
                    confidence REAL NOT NULL,
                    verification TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_entities (
                    event_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    PRIMARY KEY (event_id, name, entity_type),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_sources (
                    event_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    PRIMARY KEY (event_id, source_id),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_evidence (
                    event_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    PRIMARY KEY (event_id, source_id, evidence_type, description),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_occurred_at ON events(occurred_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_verification ON events(verification)")

    def save(self, event: Event) -> None:
        """Insert or fully replace an event and its child records."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    id, event_type, title, description, location_text, country,
                    city, latitude, longitude, occurred_at, severity, confidence,
                    verification
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    event_type = excluded.event_type,
                    title = excluded.title,
                    description = excluded.description,
                    location_text = excluded.location_text,
                    country = excluded.country,
                    city = excluded.city,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    occurred_at = excluded.occurred_at,
                    severity = excluded.severity,
                    confidence = excluded.confidence,
                    verification = excluded.verification
                """,
                (
                    event.id, event.event_type.value, event.title, event.description,
                    event.location_text, event.country, event.city, event.latitude,
                    event.longitude, event.occurred_at.isoformat() if event.occurred_at else None,
                    event.severity, event.confidence, event.verification.value,
                ),
            )
            conn.execute("DELETE FROM event_entities WHERE event_id = ?", (event.id,))
            conn.execute("DELETE FROM event_sources WHERE event_id = ?", (event.id,))
            conn.execute("DELETE FROM event_evidence WHERE event_id = ?", (event.id,))
            conn.executemany(
                "INSERT INTO event_entities (event_id, name, entity_type) VALUES (?, ?, ?)",
                [(event.id, entity.name, entity.entity_type) for entity in event.entities],
            )
            conn.executemany(
                "INSERT INTO event_sources (event_id, source_id) VALUES (?, ?)",
                [(event.id, source_id) for source_id in event.source_ids],
            )
            conn.executemany(
                """
                INSERT INTO event_evidence (
                    event_id, source_id, evidence_type, description, confidence
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (event.id, evidence.source_id, evidence.evidence_type.value,
                     evidence.description, evidence.confidence)
                    for evidence in event.evidence
                ],
            )

    def get(self, event_id: str) -> Event | None:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
            if row is None:
                return None
            entities = conn.execute(
                "SELECT name, entity_type FROM event_entities WHERE event_id = ?", (event_id,)
            ).fetchall()
            sources = conn.execute(
                "SELECT source_id FROM event_sources WHERE event_id = ?", (event_id,)
            ).fetchall()
            evidence_rows = conn.execute(
                "SELECT source_id, evidence_type, description, confidence FROM event_evidence WHERE event_id = ?",
                (event_id,),
            ).fetchall()

        payload = dict(row)
        payload["entities"] = [EventEntity(**dict(item)) for item in entities]
        payload["source_ids"] = [item["source_id"] for item in sources]
        payload["evidence"] = [
            Evidence(source_id=item["source_id"], evidence_type=item["evidence_type"],
                     description=item["description"], confidence=item["confidence"])
            for item in evidence_rows
        ]
        return Event.model_validate(payload)

    def list_recent(self, limit: int = 20) -> list[Event]:
        if limit < 1:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM events ORDER BY occurred_at DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [event for row in rows if (event := self.get(row[0])) is not None]

    def list_all(self) -> list[Event]:
        """Return every persisted event, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM events ORDER BY occurred_at DESC, id DESC"
            ).fetchall()
        return [event for row in rows if (event := self.get(row[0])) is not None]

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
