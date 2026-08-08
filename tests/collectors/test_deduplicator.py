from iran_monitor.collectors.deduplicator import NewsDeduplicator
from iran_monitor.models.news import NewsItem


def make_item(item_id: str, content_hash: str) -> NewsItem:
    return NewsItem(
        id=item_id,
        source_name="test",
        source_type="rss",
        language="en",
        title="Test",
        text="Test news",
        content_hash=content_hash,
    )


def test_deduplicator_removes_duplicates():
    items = [
        make_item("1", "hash-a"),
        make_item("2", "hash-a"),
        make_item("3", "hash-b"),
    ]

    result = NewsDeduplicator().deduplicate(items)

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "3"


def test_deduplicator_keeps_unique_items():
    items = [
        make_item("1", "hash-a"),
        make_item("2", "hash-b"),
    ]

    result = NewsDeduplicator().deduplicate(items)

    assert len(result) == 2
