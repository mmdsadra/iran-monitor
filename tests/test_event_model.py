import pytest
from pydantic import ValidationError

from iran_monitor.events.model import Event, EventType


def test_event_creation():
    event = Event(
        id="event-001",
        event_type=EventType.EXPLOSION,
        description="Explosion reported near Mehrabad Airport",
        location_text="Mehrabad Airport",
        city="Tehran",
        country="Iran",
        confidence=0.8,
        source_ids=["news-001"],
    )

    assert event.id == "event-001"
    assert event.event_type == EventType.EXPLOSION
    assert event.city == "Tehran"
    assert event.confidence == 0.8


def test_event_confidence_range():
    with pytest.raises(ValidationError):
        Event(
            id="event-002",
            event_type=EventType.EXPLOSION,
            description="Test",
            confidence=1.5,
        )


def test_event_defaults():
    event = Event(
        id="event-003",
        event_type=EventType.OTHER,
        description="Unknown event",
    )

    assert event.confidence == 0.0
    assert event.source_ids == []


def test_event_defaults_are_safe():
    from iran_monitor.events.model import (
        Event,
        EventType,
        VerificationStatus,
    )

    event = Event(
        id="event-001",
        event_type=EventType.EXPLOSION,
        description="Reported explosion in Isfahan.",
    )

    assert event.confidence == 0.0
    assert event.severity == 0.0
    assert event.verification == VerificationStatus.UNVERIFIED
    assert event.entities == []
    assert event.evidence == []
    assert event.source_ids == []


def test_event_rejects_invalid_confidence():
    import pytest
    from pydantic import ValidationError

    from iran_monitor.events.model import Event, EventType

    with pytest.raises(ValidationError):
        Event(
            id="event-002",
            event_type=EventType.EXPLOSION,
            description="Test",
            confidence=1.5,
        )


def test_event_can_store_claim_evidence():
    from iran_monitor.events.model import (
        Event,
        EventEntity,
        EventType,
        VerificationStatus,
    )

    event = Event(
        id="event-003",
        event_type=EventType.EXPLOSION,
        description="An explosion was reportedly heard.",
        city="Isfahan",
        verification=VerificationStatus.UNVERIFIED,
        entities=[
            EventEntity(
                name="Isfahan",
                entity_type="location",
            )
        ],
        evidence=[
            "Source reported an explosion in Isfahan."
        ],
        source_ids=["telegram:12345"],
    )

    assert event.city == "Isfahan"
    assert event.verification == VerificationStatus.UNVERIFIED
    assert len(event.entities) == 1
    assert len(event.evidence) == 1
    assert event.source_ids == ["telegram:12345"]
