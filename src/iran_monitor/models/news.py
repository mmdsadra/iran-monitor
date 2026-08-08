from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


class NewsItem(BaseModel):
    id: str
    source_name: str
    source_type: str

    language: str | None = None
    title: str | None = None
    text: str
    url: str | None = None

    published_at: datetime | None = None

    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    content_hash: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("NewsItem.text must not be empty")

        return value

    def model_post_init(self, __context: Any) -> None:
        if self.content_hash is None:
            import hashlib

            content = (
                f"{self.source_name}|"
                f"{self.title or ''}|"
                f"{self.text}"
            )

            self.content_hash = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()