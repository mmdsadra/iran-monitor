from datetime import datetime, timezone

from iran_monitor.events.model import Event, EventEntity, EventType, VerificationStatus
from iran_monitor.intelligence.evidence import Evidence, EvidenceType
from iran_monitor.storage.events import EventRepository


def make_event(event_id="event-1"):
    return Event(
        id=event_id,
        event_type=EventType.EXPLOSION,
        title="Explosion in Isfahan",
        description="An explosion was reported in Isfahan.",
        location_text="Isfahan",
        country="Iran",
        city="Isfahan",
        latitude=32.6546,
        longitude=51.6680,
        occurred_at=datetime(2026, 8, 8, 12, 30, tzinfo=timezone.utc),
        severity=0.8,
        confidence=0.7,
        verification=VerificationStatus.CORROBORATED,
        entities=[EventEntity(name="Isfahan", entity_type="location")],
        source_ids=["news-1", "news-2"],
        evidence=[
            Evidence(
                source_id="news-1",
                evidence_type=EvidenceType.DIRECT_REPORT,
                description="Direct report from source 1.",
                confidence=0.7,
            ),
            Evidence(
                source_id="news-2",
                evidence_type=EvidenceType.CORROBORATION,
                description="Independent corroborating report.",
                confidence=0.8,
            ),
        ],
    )


def test_event_round_trip(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    event = make_event()

    repo.save(event)
    loaded = repo.get(event.id)

    assert loaded == event
    assert repo.count() == 1


def test_save_updates_existing_event(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    event = make_event()
    repo.save(event)

    updated = event.model_copy(
        update={
            "title": "Updated explosion report",
            "confidence": 0.95,
            "verification": VerificationStatus.VERIFIED,
            "source_ids": ["news-1", "news-2", "news-3"],
            "evidence": [
                Evidence(
                    source_id="news-3",
                    evidence_type=EvidenceType.OFFICIAL_STATEMENT,
                    description="Official statement.",
                    confidence=0.95,
                )
            ],
        }
    )
    repo.save(updated)

    assert repo.count() == 1
    assert repo.get(event.id) == updated


def test_list_recent_orders_by_occurred_at(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(make_event("old"))
    repo.save(
        make_event("new").model_copy(
            update={"occurred_at": datetime(2026, 8, 9, 12, 30, tzinfo=timezone.utc)}
        )
    )

    events = repo.list_recent(limit=2)

    assert [event.id for event in events] == ["new", "old"]


def test_missing_event_returns_none(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))

    assert repo.get("missing") is None
