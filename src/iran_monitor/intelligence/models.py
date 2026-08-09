from enum import Enum

from pydantic import BaseModel


class RejectionReason(str, Enum):
    GAMBLING = "gambling"
    ADVERTISEMENT = "advertisement"
    SPAM = "spam"
    IRRELEVANT = "irrelevant"


class GateDecision(BaseModel):
    accepted: bool
    reason: RejectionReason | None = None
    score: float = 0.0
