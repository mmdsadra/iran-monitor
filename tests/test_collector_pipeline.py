from iran_monitor.models.news import NewsItem
from iran_monitor.pipeline.collector_pipeline import CollectorPipeline


class FakeCollector:
    def __init__(self, items):
        self.items = items

    def collect(self):
        return self.items


def make_item(item_id: str, content_hash: str) -> NewsItem:
    return NewsItem(
        id=item_id,
        source_name="test",
        source_type="test",
        language="en",
        title="Test",
        text="Test",
        content_hash=content_hash,
    )


def test_pipeline_collects_and_deduplicates():
    collector_a = FakeCollector(
        [
            make_item("1", "hash-a"),
            make_item("2", "hash-b"),
        ]
    )

    collector_b = FakeCollector(
        [
            make_item("3", "hash-b"),
            make_item("4", "hash-c"),
        ]
    )

    pipeline = CollectorPipeline(
        collectors=[collector_a, collector_b]
    )

    result = pipeline.run()

    assert len(result) == 3

    assert [item.id for item in result] == [
        "1",
        "2",
        "4",
    ]
