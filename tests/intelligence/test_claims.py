from datetime import datetime, timezone

import pytest

from iran_monitor.events.model import EventType
from iran_monitor.intelligence.claims import (
    Evidence,
    EventClaim,
    VerificationStatus,
    claim_from_news,
)
from iran_monitor.models.news import NewsItem


def make_news() -> NewsItem:
    return NewsItem(
        id="telegram:123",
        source_name="test",
        source_type="telegram",
        language="fa",
        text="گزارش وقوع انفجار در اصفهان",
        url="https://example.com/123",
        published_at=datetime.now(timezone.utc),
    )


def test_evidence_requires_text():
    with pytest.raises(ValueError):
        Evidence(
            source_id="telegram:123",
            text="   ",
        )


def test_claim_validates_confidence():
    with pytest.raises(ValueError):
        EventClaim(
            id="claim:1",
            event_type=EventType.EXPLOSION,
            description="Explosion reported",
            source_id="telegram:123",
            confidence=1.5,
        )


def test_claim_starts_unverified():
    claim = EventClaim(
        id="claim:1",
        event_type=EventType.EXPLOSION,
        description="Explosion reported",
        source_id="telegram:123",
    )

    assert claim.verification == VerificationStatus.UNVERIFIED


def test_claim_can_store_evidence():
    evidence = Evidence(
        source_id="telegram:123",
        text="Explosion reported in Isfahan.",
    )

    claim = EventClaim(
        id="claim:1",
        event_type=EventType.EXPLOSION,
        description="Explosion reported",
        source_id="telegram:123",
        evidence=(evidence,),
    )

    assert len(claim.evidence) == 1
    assert claim.evidence[0].source_id == "telegram:123"


def test_claim_from_news_preserves_original_evidence():
    item = make_news()

    claim = claim_from_news(
        item,
        event_type=EventType.EXPLOSION,
        description="Explosion reported in Isfahan.",
        city="Isfahan",
        confidence=0.8,
    )

    assert claim.id == "claim:telegram:123"
    assert claim.source_id == item.id
    assert claim.city == "Isfahan"
    assert claim.confidence == 0.8
    assert len(claim.evidence) == 1
    assert claim.evidence[0].text == item.text
    assert claim.evidence[0].url == item.url
