import asyncio
from pathlib import Path

from iran_monitor.collectors.telegram import TelegramCollector
from iran_monitor.collectors.telegram_auth import (
    create_telegram_client,
)
from iran_monitor.config.environment import load_environment
from iran_monitor.config.loader import load_sources
from iran_monitor.storage.sqlite import SQLiteStorage


async def main() -> None:
    load_environment()

    config = load_sources(
        Path("config/local/sources.yaml")
    )

    telegram_sources = [
        source
        for source in config.telegram
        if source.enabled
    ]

    if not telegram_sources:
        print("No enabled Telegram sources.")
        return

    client = create_telegram_client()

    with SQLiteStorage() as storage:
        async with client:
            for source in telegram_sources:
                print()
                print(f"Collecting: {source.name}")

                collector = TelegramCollector(
                    client,
                    source_name=source.name,
                    username=source.username,
                    language=source.language,
                    limit=10,
                )

                last_message_id = storage.get_last_message_id(
                    source.name
                )

                if last_message_id is None:
                    latest_id = await collector.get_latest_message_id()

                    if latest_id is None:
                        print("Channel has no messages.")
                        continue

                    storage.update_source_state(
                        source_name=source.name,
                        source_type="telegram",
                        last_message_id=latest_id,
                    )

                    print(
                        f"Initialized source at message ID: {latest_id}"
                    )

                    continue

                print(f"Last message ID: {last_message_id}")

                items = await collector.collect(
                    min_id=last_message_id
                )

                inserted = storage.save_many(items)

                if items:
                    newest_message_id = max(
                        item.raw_data["message_id"]
                        for item in items
                    )

                    storage.update_source_state(
                        source_name=source.name,
                        source_type="telegram",
                        last_message_id=newest_message_id,
                    )

                print(f"Fetched:   {len(items)}")
                print(f"Inserted:  {inserted}")
                print(f"Duplicate: {len(items) - inserted}")
                print(f"Database:  {storage.count()}")


if __name__ == "__main__":
    asyncio.run(main())
