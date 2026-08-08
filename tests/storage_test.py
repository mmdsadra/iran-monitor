from datetime import datetime, timezone

from iran_monitor.models.news import NewsItem
from iran_monitor.storage.sqlite import SQLiteStorage


def make_item() -> NewsItem:
    return NewsItem(
        id="test-id",
        source_name="test",
        source_type="telegram",
        language="fa",
        title="Test",
        text="Test message",
        url="https://example.com/test",
        published_at=datetime.now(timezone.utc),
        content_hash="test-hash",
        raw_data={"message_id": 1},
    )


def test_storage_insert_and_deduplicate(tmp_path):
    db = tmp_path / "test.db"

    with SQLiteStorage(db) as storage:
        item = make_item()

        assert storage.save(item) is True
        assert storage.save(item) is False
        assert storage.count() == 1
