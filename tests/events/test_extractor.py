from datetime import datetime, timezone

from iran_monitor.events.extractor import EventExtractor
from iran_monitor.events.model import EventType
from iran_monitor.models.news import NewsItem


def make_item(text: str, title: str | None = None) -> NewsItem:
    return NewsItem(
        id="test-001",
        source_name="test",
        source_type="telegram",
        language="fa",
        title=title,
        text=text,
        published_at=datetime.now(timezone.utc),
    )


def test_extracts_persian_explosion():
    item = make_item(
        "انفجار شدیدی در یک مرکز صنعتی رخ داد",
        "انفجار در مرکز صنعتی",
    )

    event = EventExtractor().extract(item)

    assert event is not None
    assert event.event_type == EventType.EXPLOSION
    assert event.source_ids == ["test-001"]
    assert event.confidence > 0.0


def test_extracts_fire():
    item = make_item("در این منطقه آتش‌سوزی رخ داده است")

    event = EventExtractor().extract(item)

    assert event is not None
    assert event.event_type == EventType.FIRE


def test_extracts_attack():
    item = make_item("این منطقه مورد حمله قرار گرفت")

    event = EventExtractor().extract(item)

    assert event is not None
    assert event.event_type == EventType.ATTACK


def test_ignores_non_event_news():
    item = make_item("قیمت دلار امروز افزایش پیدا کرد")

    event = EventExtractor().extract(item)

    assert event is None


def test_event_id_is_stable():
    extractor = EventExtractor()
    item = make_item("انفجار در یک منطقه")

    event_a = extractor.extract(item)
    event_b = extractor.extract(item)

    assert event_a is not None
    assert event_b is not None
    assert event_a.id == event_b.id
