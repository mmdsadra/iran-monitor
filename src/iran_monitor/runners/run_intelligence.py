import argparse
import asyncio
from pathlib import Path

from iran_monitor.collectors.rss import RSSCollector
from iran_monitor.collectors.telegram import TelegramCollector
from iran_monitor.collectors.telegram_auth import create_telegram_client
from iran_monitor.config.environment import load_environment
from iran_monitor.config.loader import load_sources
from iran_monitor.events.pipeline import EventIntelligencePipeline
from iran_monitor.intelligence.config import LLMConfig
from iran_monitor.intelligence.pipeline import IntelligencePipeline
from iran_monitor.intelligence.providers.openai import OpenAIProvider
from iran_monitor.models.news import NewsItem
from iran_monitor.output.feed import IntelligenceFeedBuilder
from iran_monitor.output.telegram import TelegramPublisher
from iran_monitor.storage.events import EventRepository
from iran_monitor.storage.sqlite import SQLiteStorage


DEFAULT_SOURCE_LIMIT = 150


def process_items(
    items: list[NewsItem],
    intelligence: IntelligencePipeline,
    events: EventIntelligencePipeline,
) -> tuple[int, int, list]:
    accepted = 0
    created_or_merged = 0
    results = []

    for item in items:
        result = intelligence.process(item)
        if result.status != "accepted" or result.claim is None:
            continue

        accepted += 1
        event_result = events.process(result.claim)
        created_or_merged += 1
        results.append(event_result)

    return accepted, created_or_merged, results


async def collect_telegram(config, storage: SQLiteStorage) -> list[NewsItem]:
    sources = [source for source in config.telegram if source.enabled]
    if not sources:
        return []

    client = create_telegram_client()
    items: list[NewsItem] = []

    async with client:
        for source in sources:
            collector = TelegramCollector(
                client,
                source_name=source.name,
                username=source.username,
                language=source.language,
                limit=DEFAULT_SOURCE_LIMIT,
            )
            last_id = storage.get_last_message_id(source.name)

            # First run: deliberately inspect recent history instead of only
            # recording the newest message. This gives intelligence enough
            # context to build a useful initial event picture.
            min_id = last_id or 0
            new_items = await collector.collect(min_id=min_id)
            items.extend(new_items)

            if new_items:
                newest_id = max(item.raw_data["message_id"] for item in new_items)
                storage.update_source_state(source.name, "telegram", newest_id)

    return items


def collect_rss(config) -> list[NewsItem]:
    items: list[NewsItem] = []
    for source in config.rss:
        if source.enabled:
            items.extend(RSSCollector(source).collect()[:DEFAULT_SOURCE_LIMIT])
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Iran Monitor intelligence pipeline")
    parser.add_argument("--publish", action="store_true", help="publish the generated feed to Telegram")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--sources", default="config/local/sources.yaml")
    parser.add_argument(
        "--source-limit",
        type=int,
        default=DEFAULT_SOURCE_LIMIT,
        help="maximum recent items inspected per source (default: 150)",
    )
    args = parser.parse_args()
    if args.source_limit < 1:
        parser.error("--source-limit must be positive")

    load_environment()
    config = load_sources(args.sources)
    llm = IntelligencePipeline(OpenAIProvider(LLMConfig.from_environment()))

    with SQLiteStorage("news.db") as news_storage:
        rss_items = collect_rss(config)
        telegram_items = asyncio.run(collect_telegram(config, news_storage))
        items = rss_items + telegram_items
        news_storage.save_many(items)

    repository = EventRepository("events.db")
    event_pipeline = EventIntelligencePipeline(repository)
    accepted, processed, _ = process_items(items, llm, event_pipeline)

    events = repository.list_recent(100)
    feed = IntelligenceFeedBuilder().build(events, Path(args.output_dir))

    print(f"Collected: {len(items)}")
    print(f"Accepted claims: {accepted}")
    print(f"Events created/merged: {processed}")
    print(feed.report)
    print(f"Map: {feed.map_path}")
    print(f"Assessment: {feed.assessment_path}")
    print(f"Pie: {feed.pie_path}")

    if args.publish:
        TelegramPublisher().publish(
            feed.report,
            feed.map_path,
            feed.assessment_path,
            feed.pie_path,
        )
        print("Published to Telegram.")


if __name__ == "__main__":
    main()
