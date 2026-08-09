from datetime import datetime

from pydantic import BaseModel, Field

from iran_monitor.events.model import EventType


class EventClaim(BaseModel):
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
