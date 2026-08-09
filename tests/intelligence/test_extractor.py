from datetime import datetime, timezone

from iran_monitor.events.model import EventType
from iran_monitor.intelligence.extractor import MockIntelligenceProvider
from iran_monitor.models.news import NewsItem


def make_news() -> NewsItem:
    return NewsItem(
        id="news-001",
        source_name="test",
        source_type="telegram",
        language="fa",
        title="انفجار در یک منطقه",
        text="یک انفجار گزارش شده است.",
        published_at=datetime.now(timezone.utc),
    )


def test_mock_provider_returns_event():
    provider = MockIntelligenceProvider()

    event = provider.analyze(make_news())

    assert event is not None
    assert event.id == "event-news-001"
    assert event.event_type == EventType.OTHER
    assert event.source_ids == ["news-001"]


def test_mock_provider_does_not_call_external_services():
    provider = MockIntelligenceProvider()

    event = provider.analyze(make_news())

    assert event.confidence == 0.0