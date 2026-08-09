from iran_monitor.classification.classifier import EventClassifier
from iran_monitor.classification.models import EventCategory, EventType
from iran_monitor.models.news import NewsItem


def make_item(text: str) -> NewsItem:
    return NewsItem(
        id="test",
        source_name="test",
        source_type="telegram",
        language="fa",
        text=text,
    )


def test_explosion_classification():
    result = EventClassifier().classify(
        make_item("گزارش انفجار در نزدیکی یک مرکز صنعتی")
    )

    assert result.category == EventCategory.SECURITY
    assert result.event_type == EventType.EXPLOSION
    assert result.confidence > 0.8


def test_negotiation_classification():
    result = EventClassifier().classify(
        make_item("مذاکرات ایران و عمان ادامه پیدا کرد")
    )

    assert result.category == EventCategory.POLITICAL
    assert result.event_type == EventType.NEGOTIATION


def test_protest_classification():
    result = EventClassifier().classify(
        make_item("اعتراضات در چند شهر ادامه داشت")
    )

    assert result.category == EventCategory.CIVIL
    assert result.event_type == EventType.PROTEST


def test_unknown_event():
    result = EventClassifier().classify(
        make_item("یک خبر عمومی بدون نوع رویداد مشخص")
    )

    assert result.category == EventCategory.OTHER
    assert result.event_type == EventType.UNKNOWN
    assert result.confidence < 0.5
