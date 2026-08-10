from dataclasses import dataclass
from uuid import uuid4

from iran_monitor.events.matcher import EventMatcher
from iran_monitor.events.model import Event, EventEntity, EventType, VerificationStatus
from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.intelligence.evidence import Evidence, EvidenceType
from iran_monitor.storage.events import EventRepository


@dataclass(frozen=True)
class ClusterResult:
    event: Event
    created: bool
    match_score: float | None = None


SEVERITY_BY_TYPE = {
    EventType.MISSILE_LAUNCH: 0.88,
    EventType.AIRSTRIKE: 0.92,
    EventType.STRIKE: 0.86,
    EventType.ATTACK: 0.82,
    EventType.EXPLOSION: 0.68,
    EventType.CASUALTY: 0.78,
    EventType.INFRASTRUCTURE_DAMAGE: 0.70,
    EventType.MILITARY_MOVEMENT: 0.58,
    EventType.PROTEST: 0.42,
    EventType.FIRE: 0.30,
    EventType.DIPLOMACY: 0.18,
    EventType.OTHER: 0.10,
}


class EventClusterer:
    """Merge incoming claims into existing events or create new events."""

    def __init__(self, repository: EventRepository, matcher=None):
        self.repository = repository
        self.matcher = matcher or EventMatcher(repository)

    def process_claim(self, claim: EventClaim) -> ClusterResult:
        match = self.matcher.find_match(claim)
        if match is None:
            event = self._new_event(claim)
            self.repository.save(event)
            return ClusterResult(event=event, created=True)
        merged = self.merge(match.event, claim)
        self.repository.save(merged)
        return ClusterResult(event=merged, created=False, match_score=match.score)

    def merge(self, event: Event, claim: EventClaim) -> Event:
        source_ids = list(dict.fromkeys(event.source_ids))
        for source_id in self._claim_source_ids(claim):
            if source_id not in source_ids:
                source_ids.append(source_id)

        evidence = list(event.evidence)
        existing_evidence = {(item.source_id, item.evidence_type, item.description) for item in evidence}
        for item in self._claim_evidence(claim):
            key = (item.source_id, item.evidence_type, item.description)
            if key not in existing_evidence:
                evidence.append(item)
                existing_evidence.add(key)

        entities = list(event.entities)
        existing_entities = {(item.name.lower(), item.entity_type) for item in entities}
        for entity in self._claim_entities(claim):
            key = (entity.name.lower(), entity.entity_type)
            if key not in existing_entities:
                entities.append(entity)
                existing_entities.add(key)

        confidence = self._combined_confidence(event.confidence, claim.confidence, source_ids, event.source_ids)
        return event.model_copy(update={
            "title": event.title or claim.description,
            "description": self._merge_description(event.description, claim.description),
            "location_text": event.location_text or claim.location_text,
            "country": event.country or claim.country,
            "city": event.city or claim.city,
            "occurred_at": event.occurred_at or claim.occurred_at,
            "severity": max(event.severity, self._severity_for(claim.event_type)),
            "confidence": confidence,
            "verification": self._verification_for_sources(source_ids),
            "entities": entities,
            "evidence": evidence,
            "source_ids": source_ids,
        })

    def _new_event(self, claim: EventClaim) -> Event:
        source_ids = self._claim_source_ids(claim)
        event_id = f"event:{claim.id}" if claim.id else f"event:{uuid4()}"
        return Event(
            id=event_id,
            event_type=claim.event_type,
            title=claim.description,
            description=claim.description,
            location_text=claim.location_text,
            country=claim.country,
            city=claim.city,
            occurred_at=claim.occurred_at,
            severity=self._severity_for(claim.event_type),
            confidence=claim.confidence,
            verification=self._verification_for_sources(source_ids),
            evidence=self._claim_evidence(claim),
            source_ids=source_ids,
        )

    @staticmethod
    def _severity_for(event_type: EventType) -> float:
        return SEVERITY_BY_TYPE.get(event_type, 0.10)

    @staticmethod
    def _claim_source_ids(claim: EventClaim) -> list[str]:
        ids = [item.source_id for item in claim.evidence if item.source_id]
        if claim.source_id:
            ids.append(claim.source_id)
        return list(dict.fromkeys(ids))

    @staticmethod
    def _claim_evidence(claim: EventClaim) -> list[Evidence]:
        return [Evidence(source_id=item.source_id, evidence_type=EvidenceType.DIRECT_REPORT, description=item.text, confidence=claim.confidence) for item in claim.evidence]

    @staticmethod
    def _claim_entities(claim: EventClaim) -> list[EventEntity]:
        entities: list[EventEntity] = []
        if claim.city:
            entities.append(EventEntity(name=claim.city, entity_type="location"))
        if claim.country:
            entities.append(EventEntity(name=claim.country, entity_type="country"))
        return entities

    @staticmethod
    def _combined_confidence(current: float, incoming: float, all_sources: list[str], previous_sources: list[str]) -> float:
        if not incoming:
            return current
        if not (set(all_sources) - set(previous_sources)):
            return max(current, incoming)
        return min(1.0, 1.0 - (1.0 - current) * (1.0 - incoming))

    @staticmethod
    def _verification_for_sources(source_ids: list[str]) -> VerificationStatus:
        return VerificationStatus.CORROBORATED if len(set(source_ids)) >= 2 else VerificationStatus.UNVERIFIED

    @staticmethod
    def _merge_description(current: str, incoming: str) -> str:
        if not incoming or incoming == current:
            return current
        return f"{current} | {incoming}"
