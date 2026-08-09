from iran_monitor.intelligence.gate import IntelligenceGate
from iran_monitor.models.news import NewsItem


def make_item(text: str) -> NewsItem:
    return NewsItem(
        id="test",
        source_name="test",
        source_type="telegram",
        language="fa",
        text=text,
    )


def test_gambling_is_rejected():
    item = make_item(
        "همین امشب با اولین شارژ شانس خود را امتحان کن و "
        "در سایت پوکر جایزه ببر"
    )

    decision = IntelligenceGate().evaluate(item)

    assert decision.accepted is False
    assert decision.reason == "gambling"


def test_advertisement_is_rejected():
    item = make_item(
        "همین الان ثبت نام کن و هدیه ویژه دریافت کن"
    )

    decision = IntelligenceGate().evaluate(item)

    assert decision.accepted is False
    assert decision.reason == "advertisement"


def test_real_news_is_accepted():
    item = make_item(
        "گزارش‌هایی از وقوع انفجار در نزدیکی یک تأسیسات صنعتی منتشر شده است"
    )

    decision = IntelligenceGate().evaluate(item)

    assert decision.accepted is True
    assert decision.reason is None
