from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """
    Standardized representation of a collected news item.
    """

    id: str

    source_name: str
    source_type: str
    language: str

    title: str | None = None
    text: str

    url: str | None = None

    published_at: datetime | None = None
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    content_hash: str | None = None

    raw_data: dict[str, Any] = Field(default_factory=dict)