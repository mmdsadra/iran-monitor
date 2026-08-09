from dataclasses import dataclass
from iran_monitor.events.model import Event, EventType


@dataclass(frozen=True)
class SituationAssessment:
    overall: float
    war: float
    diplomacy: float
    protests: float
    military: float
    infrastructure: float
    casualties: float


def assess_events(events: list[Event]) -> SituationAssessment:
    """Convert recent events into deterministic 0..100 situation indicators.

    These are monitoring indicators, not probabilities of future war. Scores are
    intentionally explainable and should be replaced/extended with calibrated
    models when enough historical data exists.
    """
    if not events:
        return SituationAssessment(0, 0, 0, 0, 0, 0, 0)

    def avg_weight(predicate, weight=1.0):
        selected = [e for e in events if predicate(e)]
        if not selected:
            return 0.0
        return min(100.0, sum((0.35 + 0.65 * e.confidence) * weight * max(e.severity, 0.25) for e in selected) * 100 / len(events))

    war = min(100.0, avg_weight(lambda e: e.event_type in {
        EventType.STRIKE, EventType.ATTACK, EventType.AIRSTRIKE,
        EventType.MISSILE_LAUNCH, EventType.MILITARY_MOVEMENT,
    }, 1.15))
    diplomacy = min(100.0, avg_weight(lambda e: e.event_type == EventType.OTHER, 0.25))
    protests = avg_weight(lambda e: e.event_type == EventType.PROTEST, 1.0)
    military = avg_weight(lambda e: e.event_type in {
        EventType.MILITARY_MOVEMENT, EventType.MISSILE_LAUNCH,
        EventType.AIRSTRIKE, EventType.STRIKE,
    }, 1.0)
    infrastructure = avg_weight(lambda e: e.event_type == EventType.INFRASTRUCTURE_DAMAGE, 1.0)
    casualties = avg_weight(lambda e: e.event_type == EventType.CASUALTY, 1.2)

    overall = min(100.0, war * 0.35 + protests * 0.15 + military * 0.20 + infrastructure * 0.10 + casualties * 0.20)
    return SituationAssessment(overall, war, diplomacy, protests, military, infrastructure, casualties)
