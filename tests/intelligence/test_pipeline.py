from datetime import datetime, timezone

from iran_monitor.intelligence.pipeline import IntelligencePipeline
from iran_monitor.models.news import NewsItem


def make_news(text: str) -> NewsItem:
    return NewsItem(
        id="news-001",
        source_name="test",
        source_type="telegram",
        language="fa",
        text=text,
        published_at=datetime.now(timezone.utc),
    )


class FakeProvider:
    def __init__(self, result=None):
        self.result = result
        self.calls = 0

    def analyze(self, item):
        self.calls += 1
        return self.result


def test_gambling_is_rejected_before_llm():
    provider = FakeProvider()
    pipeline = IntelligencePipeline(provider)

    result = pipeline.process(
        make_news("ثبت نام کازینو و شرط بندی با جایزه ویژه")
    )

    assert result.status == "rejected"
    assert provider.calls == 0


def test_advertisement_is_rejected_before_llm():
    provider = FakeProvider()
    pipeline = IntelligencePipeline(provider)

    result = pipeline.process(
        make_news("همین الان ثبت نام کن و جایزه نقدی بگیر")
    )

    assert result.status == "rejected"
    assert provider.calls == 0


def test_accepted_news_reaches_llm():
    provider = FakeProvider()
    pipeline = IntelligencePipeline(provider)

    result = pipeline.process(
        make_news("گزارش وقوع انفجار در اصفهان")
    )

    assert provider.calls == 1
    assert result.status == "no_event"