from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from iran_monitor.events.model import EventType
from iran_monitor.models.news import NewsItem


class VerificationStatus(str):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class Evidence(BaseModel):
    source_id: str
    text: str
    url: str | None = None
    published_at: datetime | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Evidence.text must not be empty")
        return value


class EventClaim(BaseModel):
    id: str | None = None

    event_type: EventType
    description: str

    location_text: str | None = None
    country: str | None = None
    city: str | None = None

    occurred_at: datetime | None = None

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    evidence_text: str | None = None

    source_id: str | None = None
    verification: str = VerificationStatus.UNVERIFIED

    evidence: list[Evidence] = Field(default_factory=list)


def claim_from_news(
    item: NewsItem,
    *,
    event_type: EventType,
    description: str,
    confidence: float = 0.0,
    location_text: str | None = None,
    country: str | None = None,
    city: str | None = None,
    occurred_at: datetime | None = None,
) -> EventClaim:
    evidence = Evidence(
        source_id=item.id,
        text=item.text,
        url=item.url,
        published_at=item.published_at,
    )

    return EventClaim(
        id=f"claim:{item.id}",
        event_type=event_type,
        description=description,
        source_id=item.id,
        location_text=location_text,
        country=country,
        city=city,
        occurred_at=occurred_at,
        confidence=confidence,
        evidence=[evidence],
        evidence_text=item.text,
    )