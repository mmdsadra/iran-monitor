import argparse
import os

from iran_monitor.output.feed import IntelligenceFeedBuilder
from iran_monitor.output.telegram import TelegramPublisher
from iran_monitor.storage.events import EventRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and publish Iran Monitor intelligence feed")
    parser.add_argument("--db", default=os.getenv("EVENT_DB_PATH", "events.db"))
    parser.add_argument("--output-dir", default=os.getenv("OUTPUT_DIR", "output"))
    parser.add_argument("--publish", action="store_true", help="Publish the generated feed to Telegram")
    args = parser.parse_args()

    repo = EventRepository(args.db)
    events = repo.list_all()
    feed = IntelligenceFeedBuilder().build(events, args.output_dir)

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
