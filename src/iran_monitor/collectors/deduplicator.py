from iran_monitor.models.news import NewsItem


class NewsDeduplicator:
    """Remove duplicate news items."""

    def deduplicate(self, items: list[NewsItem]) -> list[NewsItem]:
        seen: set[str] = set()
        unique_items: list[NewsItem] = []

        for item in items:
            key = item.content_hash or item.id

            if key in seen:
                continue

            seen.add(key)
            unique_items.append(item)

        return unique_items
