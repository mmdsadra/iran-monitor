from pathlib import Path

from iran_monitor.collectors.rss import RSSCollector
from iran_monitor.config.loader import load_sources


def main() -> None:
    config_path = Path("config/sources.yaml")
    config = load_sources(config_path)

    for source in config.rss:
        if not source.enabled:
            continue

        print(f"\nCollecting: {source.name}")
        print(f"URL: {source.url}")

        collector = RSSCollector(source)
        items = collector.collect()

        print(f"Collected: {len(items)} items\n")

        for item in items[:5]:
            print("=" * 80)
            print(f"TITLE: {item.title}")
            print(f"DATE:  {item.published_at}")
            print(f"URL:   {item.url}")
            print(f"ID:    {item.id}")
            print()
            print(item.text[:500])


if __name__ == "__main__":
    main()
