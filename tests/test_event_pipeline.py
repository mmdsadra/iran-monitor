from datetime import datetime, timezone

from iran_monitor.events.model import EventType, VerificationStatus
from iran_monitor.events.pipeline import EventIntelligencePipeline
from iran_monitor.events.verification import SourceAssessment
from iran_monitor.intelligence.claims import EventClaim, Evidence
from iran_monitor.storage.events import EventRepository


def make_claim(claim_id, source_id, description, city="Isfahan"):
    return EventClaim(
        id=claim_id,
        event_type=EventType.EXPLOSION,
        description=description,
        country="Iran",
        city=city,
        location_text=f"{city} airport",
        occurred_at=datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc),
        confidence=0.8,
        source_id=source_id,
        evidence=[Evidence(source_id=source_id, text=description)],
    )


def test_pipeline_creates_and_persists_new_event(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    pipeline = EventIntelligencePipeline(repo)

    result = pipeline.process(make_claim("claim-1", "source-a", "Explosion near airport"))

    assert result.created is True
    assert result.match_score is None
    assert result.event.id == "event:claim-1"
    assert repo.get(result.event.id) == result.event
    assert result.event.verification == VerificationStatus.UNVERIFIED


def test_pipeline_merges_second_claim_and_reverifies(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    pipeline = EventIntelligencePipeline(repo)

    first = make_claim("claim-1", "source-a", "Explosion near airport")
    second = make_claim("claim-2", "source-b", "Explosion reported near airport")

    pipeline.process(first, [SourceAssessment("source-a", reliability=0.8)])
    result = pipeline.process(
        second,
        [
            SourceAssessment("source-a", reliability=0.8),
            SourceAssessment("source-b", reliability=0.8),
        ],
    )

    assert result.created is False
    assert result.match_score is not None
    assert result.event.id == "event:claim-1"
    assert result.event.source_ids == ["source-a", "source-b"]
    assert result.event.verification == VerificationStatus.CORROBORATED
    assert result.event.confidence >= 0.96
    assert repo.count() == 1


def test_pipeline_keeps_unrelated_claim_as_new_event(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    pipeline = EventIntelligencePipeline(repo)

    pipeline.process(make_claim("claim-1", "source-a", "Explosion in Isfahan"))
    result = pipeline.process(
        make_claim("claim-2", "source-b", "Explosion in Tehran", city="Tehran")
    )

    assert result.created is True
    assert result.event.id == "event:claim-2"
    assert repo.count() == 2
