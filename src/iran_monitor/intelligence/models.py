from enum import Enum

from pydantic import BaseModel, Field


class RejectionReason(str, Enum):
    GAMBLING = "gambling"
    ADVERTISEMENT = "advertisement"
    SPAM = "spam"
    IRRELEVANT = "irrelevant"


class GateDecision(BaseModel):
    accepted: bool
    reason: RejectionReason | None = None
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
