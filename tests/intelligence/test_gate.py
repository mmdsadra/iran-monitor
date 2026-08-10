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
    item = make_item("همین الان ثبت نام کن و هدیه ویژه دریافت کن")
    decision = IntelligenceGate().evaluate(item)
    assert decision.accepted is False
    assert decision.reason == "advertisement"


def test_iran_news_is_accepted():
    item = make_item("گزارش‌هایی از وقوع انفجار در نزدیکی یک تأسیسات صنعتی در ایران منتشر شده است")
    decision = IntelligenceGate().evaluate(item)
    assert decision.accepted is True
    assert decision.reason is None
    assert decision.relevance_score >= 0.75


def test_colombia_earthquake_is_rejected():
    item = make_item("A major earthquake damaged infrastructure in Colombia")
    decision = IntelligenceGate().evaluate(item)
    assert decision.accepted is False
    assert decision.reason == "irrelevant"
    assert decision.relevance_score == 0.0


def test_hormuz_military_story_is_accepted():
    item = make_item("US aircraft carrier movement reported near the Strait of Hormuz")
    decision = IntelligenceGate().evaluate(item)
    assert decision.accepted is True
    assert decision.relevance_score >= 0.45
