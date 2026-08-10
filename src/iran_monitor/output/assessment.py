from dataclasses import dataclass
from datetime import datetime, timezone
import math

from iran_monitor.events.model import Event, EventType, VerificationStatus


@dataclass(frozen=True)
class SituationAssessment:
    overall: float
    war: float
    diplomacy: float
    protests: float
    military: float
    infrastructure: float
    casualties: float


WAR_TYPES = {EventType.STRIKE, EventType.ATTACK, EventType.AIRSTRIKE, EventType.MISSILE_LAUNCH, EventType.EXPLOSION}
MILITARY_TYPES = {EventType.MILITARY_MOVEMENT, EventType.MISSILE_LAUNCH, EventType.AIRSTRIKE, EventType.STRIKE, EventType.ATTACK}


def _recency_weight(event: Event, now: datetime) -> float:
    if event.occurred_at is None:
        return 0.35
    occurred = event.occurred_at
    if occurred.tzinfo is None:
        occurred = occurred.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (now - occurred).total_seconds() / 3600.0)
    return max(0.08, math.exp(-age_hours / 52.0))


def _verification_weight(event: Event) -> float:
    return {VerificationStatus.UNVERIFIED: 0.72, VerificationStatus.CORROBORATED: 0.90, VerificationStatus.VERIFIED: 1.00}.get(event.verification, 0.72)


def _event_signal(event: Event, now: datetime, category_weight: float) -> float:
    severity = max(0.0, min(1.0, event.severity))
    confidence = max(0.0, min(1.0, event.confidence))
    confidence_weight = 0.45 + 0.55 * confidence
    return severity * confidence_weight * _verification_weight(event) * _recency_weight(event, now) * category_weight


def _score(events: list[Event], predicate, category_weight: float, now: datetime) -> float:
    selected = [e for e in events if predicate(e)]
    if not selected:
        return 0.0
    signal = sum(_event_signal(e, now, category_weight) for e in selected)
    return min(100.0, 100.0 * (1.0 - math.exp(-signal / 2.25)))


def assess_events(events: list[Event]) -> SituationAssessment:
    if not events:
        return SituationAssessment(0, 0, 0, 0, 0, 0, 0)
    now = datetime.now(timezone.utc)
    war = _score(events, lambda e: e.event_type in WAR_TYPES, 1.35, now)
    diplomacy = _score(events, lambda e: e.event_type == EventType.DIPLOMACY, 0.22, now)
    protests = _score(events, lambda e: e.event_type == EventType.PROTEST, 1.05, now)
    military = _score(events, lambda e: e.event_type in MILITARY_TYPES, 1.15, now)
    infrastructure = _score(events, lambda e: e.event_type == EventType.INFRASTRUCTURE_DAMAGE, 1.10, now)
    casualties = _score(events, lambda e: e.event_type == EventType.CASUALTY, 1.45, now)
    overall = min(100.0, sum(value * weight for value, weight in [
        (war, 0.35), (military, 0.20), (casualties, 0.20),
        (infrastructure, 0.10), (protests, 0.10), (diplomacy, 0.05),
    ]))
    return SituationAssessment(overall, war, diplomacy, protests, military, infrastructure, casualties)
