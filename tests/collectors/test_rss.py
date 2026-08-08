from datetime import datetime, timezone

from iran_monitor.collectors.rss import RSSCollector
from iran_monitor.config.models import RSSSource


def test_rss_collector(monkeypatch):
    class FakeFeed:
        bozo = False
        entries = [
            {
                "title": "Test News",
                "summary": "This is a test news item.",
                "link": "https://example.com/news/1",
                "published": "Sat, 08 Aug 2026 10:00:00 GMT",
            }
        ]

    monkeypatch.setattr(
        "iran_monitor.collectors.rss.feedparser.parse",
        lambda url: FakeFeed(),
    )

    source = RSSSource(
        name="test_source",
        url="https://example.com/rss",
        language="en",
        enabled=True,
    )

    collector = RSSCollector(source)
    items = collector.collect()

    assert len(items) == 1

    item = items[0]

    assert item.source_name == "test_source"
    assert item.source_type == "rss"
    assert item.language == "en"
    assert item.title == "Test News"
    assert item.text == "This is a test news item."
    assert item.url == "https://example.com/news/1"

    assert item.published_at == datetime(
        2026,
        8,
        8,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert item.content_hash
    assert item.id == item.content_hash
