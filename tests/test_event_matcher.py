from datetime import datetime, timezone

from iran_monitor.events.matcher import EventMatcher
from iran_monitor.events.model import Event, EventType
from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.storage.events import EventRepository


def make_event(event_id="event-1"):
    return Event(
        id=event_id,
        event_type=EventType.EXPLOSION,
        description="Explosion reported in Isfahan near the airport",
        country="Iran",
        city="Isfahan",
        location_text="Isfahan airport",
        occurred_at=datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc),
    )


def make_claim(**updates):
    data = {
        "event_type": EventType.EXPLOSION,
        "description": "Explosion reported in Isfahan near airport",
        "country": "Iran",
        "city": "Isfahan",
        "location_text": "Isfahan airport",
        "occurred_at": datetime(2026, 8, 9, 12, 30, tzinfo=timezone.utc),
        "confidence": 0.8,
    }
    data.update(updates)
    return EventClaim(**data)


def test_matching_claim_finds_existing_event(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(make_event())
    matcher = EventMatcher(repo)

    match = matcher.find_match(make_claim())

    assert match is not None
    assert match.event.id == "event-1"
    assert match.score >= 0.65


def test_different_event_type_does_not_match(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(make_event())
    matcher = EventMatcher(repo)

    match = matcher.find_match(make_claim(event_type=EventType.PROTEST))

    assert match is None


def test_distant_location_does_not_match(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(make_event())
    matcher = EventMatcher(repo)

    match = matcher.find_match(make_claim(city="Tehran", location_text="Tehran airport"))

    assert match is None


def test_distant_time_does_not_match(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(make_event())
    matcher = EventMatcher(repo)

    match = matcher.find_match(
        make_claim(occurred_at=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
    )

    assert match is None


def test_best_candidate_is_selected(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(make_event("weak"))
    repo.save(
        make_event("strong").model_copy(
            update={"description": "Explosion reported in Isfahan city"}
        )
    )
    matcher = EventMatcher(repo)

    match = matcher.find_match(make_claim())

    assert match is not None
    assert match.event.id == "strong"


def test_location_conflict_is_hard_mismatch_even_with_matching_text(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(
        make_event().model_copy(
            update={"description": "Explosion reported in Tehran near airport"}
        )
    )
    matcher = EventMatcher(repo)

    match = matcher.find_match(make_claim(city="Tehran", location_text="Tehran airport"))

    assert match is None


def test_time_conflict_is_hard_mismatch_even_with_matching_text(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    repo.save(
        make_event().model_copy(
            update={"description": "Explosion reported in Isfahan near airport"}
        )
    )
    matcher = EventMatcher(repo)

    match = matcher.find_match(
        make_claim(
            occurred_at=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc),
            description="Explosion reported in Isfahan near airport",
        )
    )

    assert match is None
