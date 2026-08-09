from datetime import datetime, timezone

from iran_monitor.events.model import EventType
from iran_monitor.intelligence.extractor import MockIntelligenceProvider
from iran_monitor.intelligence.gate import IntelligenceGate
from iran_monitor.intelligence.pipeline import IntelligencePipeline
from iran_monitor.models.news import NewsItem


def make_news(
    item_id: str,
    text: str,
    title: str | None = None,
) -> NewsItem:
    return NewsItem(
        id=item_id,
        source_name="test",
        source_type="telegram",
        language="fa",
        title=title,
        text=text,
        published_at=datetime.now(timezone.utc),
    )


def test_pipeline_processes_accepted_news():
    pipeline = IntelligencePipeline(
        gate=IntelligenceGate(),
        provider=MockIntelligenceProvider(),
    )

    events = pipeline.process([
        make_news("1", "گزارش یک رویداد مهم", "خبر"),
    ])

    assert len(events) == 1
    assert events[0].id == "event-1"
    assert events[0].source_ids == ["1"]


def test_pipeline_rejects_gambling():
    pipeline = IntelligencePipeline(
        gate=IntelligenceGate(),
        provider=MockIntelligenceProvider(),
    )

    events = pipeline.process([
        make_news("1", "کازینو و شرط بندی آنلاین", "تبلیغات"),
    ])

    assert events == []


def test_pipeline_processes_multiple_items():
    pipeline = IntelligencePipeline(
        gate=IntelligenceGate(),
        provider=MockIntelligenceProvider(),
    )

    events = pipeline.process([
        make_news("1", "خبر اول"),
        make_news("2", "خبر دوم"),
        make_news("3", "پوکر و شرط بندی"),
    ])

    assert len(events) == 2
    assert {event.id for event in events} == {
        "event-1",
        "event-2",
    }
