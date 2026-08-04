from datetime import datetime, timezone

from iran_monitor.models.news import NewsItem


def test_news_item_creation():
    item = NewsItem(
        id="test-001",
        source_name="Test Source",
        source_type="telegram",
        language="fa",
        text="یک خبر آزمایشی",
        published_at=datetime.now(timezone.utc),
    )

    assert item.id == "test-001"
    assert item.source_type == "telegram"
    assert item.language == "fa"
    assert item.text == "یک خبر آزمایشی"
    assert item.collected_at is not None

import pytest
from pydantic import ValidationError


def test_news_item_requires_text():
    with pytest.raises(ValidationError):
        NewsItem(
            id="test-002",
            source_name="Test Source",
            source_type="telegram",
            language="fa",
        )