from dataclasses import dataclass

from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.intelligence.gate import IntelligenceGate
from iran_monitor.intelligence.geography import normalize_claim_location
from iran_monitor.intelligence.providers.openai import OpenAIProvider
from iran_monitor.models.news import NewsItem


@dataclass(frozen=True)
class IntelligenceResult:
    news_id: str
    status: str
    claim: EventClaim | None = None
    reason: str | None = None


class IntelligencePipeline:
    def __init__(
        self,
        provider: OpenAIProvider,
        gate: IntelligenceGate | None = None,
    ):
        self.provider = provider
        self.gate = gate or IntelligenceGate()

    def process(self, item: NewsItem) -> IntelligenceResult:
        decision = self.gate.evaluate(item)

        if not decision.accepted:
            return IntelligenceResult(
                news_id=item.id,
                status="rejected",
                reason=decision.reason.value if decision.reason else None,
            )

        try:
            claim = self.provider.analyze(item)
        except Exception as exc:
            return IntelligenceResult(
                news_id=item.id,
                status="llm_error",
                reason=str(exc),
            )

        if claim is None:
            return IntelligenceResult(
                news_id=item.id,
                status="no_event",
            )

        return IntelligenceResult(
            news_id=item.id,
            status="accepted",
            claim=normalize_claim_location(claim),
        )
