from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from iran_monitor.intelligence.evidence import Evidence


class EventType(str, Enum):
    EXPLOSION = "explosion"
    FIRE = "fire"
    STRIKE = "strike"
    ATTACK = "attack"
    PROTEST = "protest"
    MILITARY_MOVEMENT = "military_movement"
    AIRSTRIKE = "airstrike"
    MISSILE_LAUNCH = "missile_launch"
    INFRASTRUCTURE_DAMAGE = "infrastructure_damage"
    CASUALTY = "casualty"
    DIPLOMACY = "diplomacy"
    OTHER = "other"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    CORROBORATED = "corroborated"
    VERIFIED = "verified"


class EventEntity(BaseModel):
    name: str
    entity_type: str


class Event(BaseModel):
    id: str
    event_type: EventType
    title: str | None = None
    description: str
    location_text: str | None = None
    country: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    occurred_at: datetime | None = None
    severity: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    verification: VerificationStatus = VerificationStatus.UNVERIFIED
    entities: list[EventEntity] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
