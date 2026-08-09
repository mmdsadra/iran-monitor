import httpx

from iran_monitor.intelligence.config import LLMConfig
from iran_monitor.intelligence.parser import (
    InvalidLLMResponse,
    parse_event_claim,
)
from iran_monitor.intelligence.prompts.event_extraction import (
    SYSTEM_PROMPT,
    build_event_extraction_prompt,
)
from iran_monitor.models.news import NewsItem


class OpenAIProvider:
    def __init__(self, config: LLMConfig):
        self.config = config

    def analyze(self, item: NewsItem):
        payload = {
            "model": self.config.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": build_event_extraction_prompt(item),
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:1000]
            raise RuntimeError(
                f"LLM request failed ({exc.response.status_code}): {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise InvalidLLMResponse(
                f"LLM response has unexpected structure: {data}"
            ) from exc

        return parse_event_claim(content)
