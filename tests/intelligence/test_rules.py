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


def test_filter_separates_iran_news_from_noise():
    items = [
        item("انفجار در نزدیکی یک مرکز صنعتی در ایران گزارش شد", "1"),
        item("همین الان شارژ کن و جایزه بگیر", "2"),
        item("گزارش جدید درباره مذاکرات ایران و آمریکا منتشر شد", "3"),
        item("A major earthquake damaged infrastructure in Colombia", "4"),
    ]

    accepted, rejected = IntelligenceGate().filter(items)

    assert len(accepted) == 2
    assert len(rejected) == 2
    assert any(decision.reason == "advertisement" for decision in rejected)
    assert any(decision.reason == "irrelevant" for decision in rejected)
