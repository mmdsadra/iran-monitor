from dataclasses import dataclass
from uuid import uuid4

from iran_monitor.events.matcher import EventMatch, EventMatcher
from iran_monitor.events.model import Event, EventEntity, VerificationStatus
from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.intelligence.evidence import Evidence, EvidenceType
from iran_monitor.storage.events import EventRepository


@dataclass(frozen=True)
class ClusterResult:
    event: Event
    created: bool
    match_score: float | None = None


class EventClusterer:
    """Merge incoming claims into existing events or create new events."""

    def __init__(self, repository: EventRepository, matcher: EventMatcher | None = None):
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
        incoming_sources = self._claim_source_ids(claim)
        for source_id in incoming_sources:
            if source_id not in source_ids:
                source_ids.append(source_id)

        evidence = list(event.evidence)
        existing_evidence = {
            (item.source_id, item.evidence_type, item.description) for item in evidence
        }
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
        verification = self._verification_for_sources(source_ids)

        return event.model_copy(
            update={
                "title": event.title or claim.description,
                "description": self._merge_description(event.description, claim.description),
                "location_text": event.location_text or claim.location_text,
                "country": event.country or claim.country,
                "city": event.city or claim.city,
                "occurred_at": event.occurred_at or claim.occurred_at,
                "confidence": confidence,
                "verification": verification,
                "entities": entities,
                "evidence": evidence,
                "source_ids": source_ids,
            }
        )

    def _new_event(self, claim: EventClaim) -> Event:
        source_ids = self._claim_source_ids(claim)
        evidence = self._claim_evidence(claim)
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
            confidence=claim.confidence,
            verification=self._verification_for_sources(source_ids),
            evidence=evidence,
            source_ids=source_ids,
        )

    @staticmethod
    def _claim_source_ids(claim: EventClaim) -> list[str]:
        ids = [item.source_id for item in claim.evidence if item.source_id]
        if claim.source_id:
            ids.append(claim.source_id)
        return list(dict.fromkeys(ids))

    @staticmethod
    def _claim_evidence(claim: EventClaim) -> list[Evidence]:
        result: list[Evidence] = []
        for item in claim.evidence:
            result.append(
                Evidence(
                    source_id=item.source_id,
                    evidence_type=EvidenceType.DIRECT_REPORT,
                    description=item.text,
                    confidence=claim.confidence,
                )
            )
        return result

    @staticmethod
    def _claim_entities(claim: EventClaim) -> list[EventEntity]:
        entities: list[EventEntity] = []
        if claim.city:
            entities.append(EventEntity(name=claim.city, entity_type="location"))
        if claim.country:
            entities.append(EventEntity(name=claim.country, entity_type="country"))
        return entities

    @staticmethod
    def _combined_confidence(
        current: float,
        incoming: float,
        all_sources: list[str],
        previous_sources: list[str],
    ) -> float:
        if not incoming:
            return current
        new_sources = set(all_sources) - set(previous_sources)
        if not new_sources:
            return max(current, incoming)
        return min(1.0, 1.0 - (1.0 - current) * (1.0 - incoming))

    @staticmethod
    def _verification_for_sources(source_ids: list[str]) -> VerificationStatus:
        if len(set(source_ids)) >= 2:
            return VerificationStatus.CORROBORATED
        return VerificationStatus.UNVERIFIED

    @staticmethod
    def _merge_description(current: str, incoming: str) -> str:
        if not incoming or incoming == current:
            return current
        return f"{current} | {incoming}"
