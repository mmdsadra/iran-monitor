from datetime import datetime, timezone

from iran_monitor.intelligence.prompts.event_extraction import (
    SYSTEM_PROMPT,
    build_event_extraction_prompt,
)
from iran_monitor.models.news import NewsItem


def test_prompt_contains_news_content():
    item = NewsItem(
        id="news-001",
        source_name="test",
        source_type="telegram",
        language="fa",
        title="انفجار در اصفهان",
        text="گزارش انفجار در یک منطقه از اصفهان",
        published_at=datetime.now(timezone.utc),
    )

    prompt = build_event_extraction_prompt(item)

    assert "انفجار در اصفهان" in prompt
    assert "گزارش انفجار" in prompt


def test_system_prompt_requires_factual_extraction():
    assert "Do not invent facts." in SYSTEM_PROMPT
    assert "structured JSON" in SYSTEM_PROMPT
