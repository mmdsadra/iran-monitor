from iran_monitor.collectors.base import BaseCollector
from iran_monitor.collectors.deduplicator import NewsDeduplicator
from iran_monitor.models.news import NewsItem


class CollectorPipeline:
    """Run collectors and normalize their output."""

    def __init__(
        self,
        collectors: list[BaseCollector],
    ):
        self.collectors = collectors
        self.deduplicator = NewsDeduplicator()

    def run(self) -> list[NewsItem]:
        collected_items: list[NewsItem] = []

        for collector in self.collectors:
            items = collector.collect()
            collected_items.extend(items)

        return self.deduplicator.deduplicate(collected_items)
