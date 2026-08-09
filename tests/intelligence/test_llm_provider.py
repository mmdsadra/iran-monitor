from datetime import datetime, timezone

import httpx

from iran_monitor.intelligence.config import LLMConfig
from iran_monitor.intelligence.providers.openai import OpenAIProvider
from iran_monitor.models.news import NewsItem


def make_item():
    return NewsItem(
        id="news-001",
        source_name="test",
        source_type="telegram",
        language="fa",
        title="انفجار در اصفهان",
        text="گزارش انفجار در اصفهان",
        published_at=datetime.now(timezone.utc),
    )


def test_provider_parses_llm_response(monkeypatch):
    config = LLMConfig(
        api_key="test-key",
        base_url="https://example.com/v1",
        model="test-model",
    )

    provider = OpenAIProvider(config)

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": """
                            {
                                "event_type": "explosion",
                                "description": "Explosion reported.",
                                "location_text": "Isfahan",
                                "country": "Iran",
                                "city": "Isfahan",
                                "occurred_at": null,
                                "confidence": 0.8,
                                "evidence_text": "Source reported an explosion."
                            }
                            """
                        }
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert kwargs["json"]["temperature"] == 0
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)

    claim = provider.analyze(make_item())

    assert claim is not None
    assert claim.city == "Isfahan"
    assert claim.confidence == 0.8


def test_provider_does_not_expose_api_key():
    config = LLMConfig(
        api_key="super-secret",
        base_url="https://example.com/v1",
        model="test-model",
    )

    assert config.api_key == "super-secret"
    assert "super-secret" not in repr(config)
