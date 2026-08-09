from iran_monitor.events.model import Event
from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.intelligence.evidence import (
    Evidence,
    EvidenceType,
)
from iran_monitor.models.news import NewsItem


def claim_to_event(
    claim: EventClaim,
    item: NewsItem,
) -> Event:

    evidence = []

    if claim.evidence_text:
        evidence.append(
            Evidence(
                source_id=item.id,
                evidence_type=EvidenceType.DIRECT_REPORT,
                description=claim.evidence_text,
                confidence=claim.confidence,
            )
        )

    return Event(
        id=f"event-{item.id}",
        event_type=claim.event_type,
        title=item.title,
        description=claim.description,
        location_text=claim.location_text,
        country=claim.country,
        city=claim.city,
        occurred_at=claim.occurred_at or item.published_at,
        confidence=claim.confidence,
        source_ids=[item.id],
        evidence=evidence,
    )
