from enum import Enum

from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    SECURITY = "security"
    POLITICAL = "political"
    CIVIL = "civil"
    INFRASTRUCTURE = "infrastructure"
    ECONOMIC = "economic"
    NATURAL_DISASTER = "natural_disaster"
    OTHER = "other"


class EventType(str, Enum):
    EXPLOSION = "explosion"
    MISSILE = "missile"
    DRONE = "drone"
    AIRSTRIKE = "airstrike"
    MILITARY_MOVEMENT = "military_movement"
    MILITARY_EXERCISE = "military_exercise"

    NEGOTIATION = "negotiation"
    GOVERNMENT_STATEMENT = "government_statement"
    DIPLOMATIC_EVENT = "diplomatic_event"
    ARREST = "arrest"
    RESIGNATION = "resignation"

    PROTEST = "protest"
    STRIKE = "strike"
    ROAD_CLOSURE = "road_closure"
    INTERNET_SHUTDOWN = "internet_shutdown"
    POWER_OUTAGE = "power_outage"

    FIRE = "fire"
    AIRPORT = "airport"
    PORT = "port"
    RAILWAY = "railway"
    FUEL_STATION = "fuel_station"

    ECONOMIC_EVENT = "economic_event"
    EARTHQUAKE = "earthquake"
    WEATHER = "weather"

    UNKNOWN = "unknown"


class ClassificationResult(BaseModel):
    category: EventCategory
    event_type: EventType
    confidence: float = Field(ge=0.0, le=1.0)
