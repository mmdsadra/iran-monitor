from datetime import datetime, timezone

from iran_monitor.events.model import EventType
from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.intelligence.validator import claim_to_event
from iran_monitor.models.news import NewsItem


def test_claim_is_converted_to_event():

    item = NewsItem(
        id="news-001",
        source_name="test",
        source_type="telegram",
        language="fa",
        title="انفجار در اصفهان",
        text="گزارش انفجار در اصفهان",
        published_at=datetime.now(timezone.utc),
    )

    claim = EventClaim(
        event_type=EventType.EXPLOSION,
        description="An explosion was reportedly heard.",
        city="Isfahan",
        confidence=0.75,
        evidence_text="Source reported an explosion in Isfahan.",
    )

    event = claim_to_event(claim, item)

    assert event.event_type == EventType.EXPLOSION
    assert event.city == "Isfahan"
    assert event.confidence == 0.75
    assert event.source_ids == ["news-001"]

    assert len(event.evidence) == 1
    assert event.evidence[0].source_id == "news-001"
