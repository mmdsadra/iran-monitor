from dataclasses import dataclass

from iran_monitor.events.model import Event, VerificationStatus


@dataclass(frozen=True)
class SourceAssessment:
    """Reliability metadata for one source supporting an event."""

    source_id: str
    reliability: float = 0.5
    independent: bool = True


@dataclass(frozen=True)
class CorroborationResult:
    confidence: float
    verification: VerificationStatus
    independent_sources: int
    total_sources: int


class EventVerificationEngine:
    """Assess event confidence and corroboration from source evidence.

    This is deliberately conservative: repeated reports from the same source do
    not count as independent corroboration, and VERIFIED is reserved for events
    with at least three independent high-reliability sources.
    """

    def __init__(
        self,
        *,
        default_reliability: float = 0.5,
        corroborated_sources: int = 2,
        verified_sources: int = 3,
        verified_reliability: float = 0.75,
    ):
        if not 0.0 <= default_reliability <= 1.0:
            raise ValueError("default_reliability must be between 0 and 1")
        if corroborated_sources < 2:
            raise ValueError("corroborated_sources must be at least 2")
        if verified_sources < corroborated_sources:
            raise ValueError("verified_sources must be >= corroborated_sources")
        if not 0.0 <= verified_reliability <= 1.0:
            raise ValueError("verified_reliability must be between 0 and 1")

        self.default_reliability = default_reliability
        self.corroborated_sources = corroborated_sources
        self.verified_sources = verified_sources
        self.verified_reliability = verified_reliability

    def assess(
        self,
        event: Event,
        assessments: list[SourceAssessment] | None = None,
    ) -> CorroborationResult:
        assessments_by_source = {
            item.source_id: item for item in (assessments or [])
        }
        source_ids = list(dict.fromkeys(event.source_ids))

        independent = [
            assessments_by_source.get(
                source_id,
                SourceAssessment(source_id=source_id, reliability=self.default_reliability),
            )
            for source_id in source_ids
        ]
        independent = [item for item in independent if item.independent]

        confidence = self._confidence(event.confidence, independent)
        independent_count = len(independent)
        total_count = len(source_ids)

        if (
            independent_count >= self.verified_sources
            and self._all_high_reliability(independent)
        ):
            verification = VerificationStatus.VERIFIED
        elif independent_count >= self.corroborated_sources:
            verification = VerificationStatus.CORROBORATED
        else:
            verification = VerificationStatus.UNVERIFIED

        return CorroborationResult(
            confidence=confidence,
            verification=verification,
            independent_sources=independent_count,
            total_sources=total_count,
        )

    def apply(
        self,
        event: Event,
        assessments: list[SourceAssessment] | None = None,
    ) -> Event:
        result = self.assess(event, assessments)
        return event.model_copy(
            update={
                "confidence": result.confidence,
                "verification": result.verification,
            }
        )

    def _confidence(
        self,
        event_confidence: float,
        sources: list[SourceAssessment],
    ) -> float:
        if not sources:
            return event_confidence

        # Combine independent source support without double-counting the same
        # source. Reliability is weighted by each source's confidence contribution.
        support = 1.0
        for source in sources:
            support *= 1.0 - max(0.0, min(1.0, source.reliability))
        combined = 1.0 - support
        return round(max(event_confidence, combined), 6)

    def _all_high_reliability(self, sources: list[SourceAssessment]) -> bool:
        return all(
            source.reliability >= self.verified_reliability for source in sources
        )
