from datetime import datetime, timezone

from iran_monitor.events.clusterer import EventClusterer
from iran_monitor.events.matcher import EventMatcher
from iran_monitor.events.model import EventType, VerificationStatus
from iran_monitor.intelligence.claims import EventClaim, Evidence
from iran_monitor.storage.events import EventRepository


def make_claim(claim_id="claim-1", source_id="news-1", description="Explosion reported in Isfahan"):
    return EventClaim(
        id=claim_id,
        event_type=EventType.EXPLOSION,
        description=description,
        country="Iran",
        city="Isfahan",
        location_text="Isfahan airport",
        occurred_at=datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc),
        confidence=0.8,
        source_id=source_id,
        evidence=[
            Evidence(
                source_id=source_id,
                text=description,
                url=f"https://example.com/{source_id}",
            )
        ],
    )


def test_first_claim_creates_event(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    clusterer = EventClusterer(repo)

    result = clusterer.process_claim(make_claim())

    assert result.created is True
    assert result.event.id == "event:claim-1"
    assert repo.count() == 1
    assert result.event.source_ids == ["news-1"]


def test_matching_claim_merges_into_existing_event(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    clusterer = EventClusterer(repo, EventMatcher(repo))
    clusterer.process_claim(make_claim("claim-1", "news-1"))

    result = clusterer.process_claim(
        make_claim("claim-2", "news-2", "Explosion reported near Isfahan airport")
    )

    assert result.created is False
    assert result.event.id == "event:claim-1"
    assert repo.count() == 1
    assert result.event.source_ids == ["news-1", "news-2"]
    assert len(result.event.evidence) == 2
    assert result.event.verification == VerificationStatus.CORROBORATED
    assert result.event.confidence > 0.8


def test_same_source_does_not_duplicate_evidence(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    clusterer = EventClusterer(repo)
    clusterer.process_claim(make_claim("claim-1", "news-1"))

    result = clusterer.process_claim(make_claim("claim-2", "news-1"))

    assert result.created is False
    assert result.event.source_ids == ["news-1"]
    assert len(result.event.evidence) == 1
    assert result.event.confidence == 0.8


def test_unrelated_claim_creates_separate_event(tmp_path):
    repo = EventRepository(str(tmp_path / "events.db"))
    clusterer = EventClusterer(repo)
    clusterer.process_claim(make_claim("claim-1", "news-1"))

    unrelated = make_claim(
        "claim-2",
        "news-2",
        "Explosion reported in Tehran airport",
    ).model_copy(update={"city": "Tehran", "location_text": "Tehran airport"})
    result = clusterer.process_claim(unrelated)

    assert result.created is True
    assert repo.count() == 2
    assert result.event.id == "event:claim-2"
