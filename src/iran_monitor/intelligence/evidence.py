from enum import Enum

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    DIRECT_REPORT = "direct_report"
    SECONDARY_REPORT = "secondary_report"
    OFFICIAL_STATEMENT = "official_statement"
    VISUAL = "visual"
    LOCATION_MATCH = "location_match"
    CORROBORATION = "corroboration"


class Evidence(BaseModel):
    source_id: str
    evidence_type: EvidenceType
    description: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
