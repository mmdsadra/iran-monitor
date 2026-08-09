from iran_monitor.intelligence.gate import IntelligenceGate
from iran_monitor.models.news import NewsItem


def item(text: str, item_id: str) -> NewsItem:
    return NewsItem(
        id=item_id,
        source_name="tribun",
        source_type="telegram",
        language="fa",
        text=text,
    )


def test_filter_separates_noise_from_news():
    items = [
        item("انفجار در نزدیکی یک مرکز صنعتی گزارش شد", "1"),
        item("همین الان شارژ کن و جایزه بگیر", "2"),
        item("گزارش جدید درباره مذاکرات منتشر شد", "3"),
    ]

    accepted, rejected = IntelligenceGate().filter(items)

    assert len(accepted) == 2
    assert len(rejected) == 1
    assert rejected[0].reason == "advertisement"
