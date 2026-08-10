import re
from dataclasses import dataclass

from iran_monitor.intelligence.claims import EventClaim, claim_from_news
from iran_monitor.intelligence.gate import IntelligenceGate
from iran_monitor.intelligence.geography import normalize_claim_location
from iran_monitor.intelligence.providers.openai import OpenAIProvider
from iran_monitor.models.news import NewsItem
from iran_monitor.events.model import EventType


@dataclass(frozen=True)
class IntelligenceResult:
    news_id: str
    status: str
    claim: EventClaim | None = None
    reason: str | None = None


_FALLBACK_PATTERNS: list[tuple[EventType, tuple[str, ...]]] = [
    (EventType.MISSILE_LAUNCH, ("missile", "موشک", "شلیک موشک", "launches a missile", "launched a missile")),
    (EventType.AIRSTRIKE, ("airstrike", "air strike", "حمله هوایی", "حملهٔ هوایی")),
    (EventType.ATTACK, ("attack", "attacked", "strike", "حمله", "مورد حمله", "حمله کردند")),
    (EventType.EXPLOSION, ("explosion", "blast", "انفجار")),
    (EventType.PROTEST, ("protest", "protests", "demonstration", "اعتراض", "اعتراضات", "تجمع", "اعتصاب")),
    (EventType.MILITARY_MOVEMENT, ("military movement", "troops", "deployment", "ناو", "نیروهای مسلح", "رزمایش", "تحرک نظامی")),
    (EventType.INFRASTRUCTURE_DAMAGE, ("infrastructure damage", "damaged infrastructure", "آسیب به زیرساخت", "آسیب به تأسیسات", "آسیب به تاسیسات")),
    (EventType.CASUALTY, ("killed", "wounded", "casualties", "تلفات", "کشته", "زخمی")),
    (EventType.DIPLOMACY, ("talks", "negotiations", "negotiation", "meeting", "met with", "diplomatic", "statement", "said", "says", "threatened", "agreement", "مذاکره", "مذاکرات", "دیدار", "گفت", "اظهار", "بیانیه", "توافق", "تهدید")),
]


def _fallback_claim(item: NewsItem) -> EventClaim | None:
    text = " ".join(part for part in [item.title or "", item.text] if part).strip()
    lowered = text.casefold()
    for event_type, signals in _FALLBACK_PATTERNS:
        if any(signal.casefold() in lowered for signal in signals):
            return claim_from_news(item, event_type=event_type, description=text[:500], confidence=0.60)
    return None


class IntelligencePipeline:
    def __init__(self, provider: OpenAIProvider, gate: IntelligenceGate | None = None):
        self.provider = provider
        self.gate = gate or IntelligenceGate()

    def process(self, item: NewsItem) -> IntelligenceResult:
        decision = self.gate.evaluate(item)
        if not decision.accepted:
            return IntelligenceResult(news_id=item.id, status="rejected", reason=decision.reason.value if decision.reason else None)

        try:
            claim = self.provider.analyze(item)
        except Exception as exc:
            return IntelligenceResult(news_id=item.id, status="llm_error", reason=str(exc))

        if claim is None:
            claim = _fallback_claim(item)
            if claim is None:
                return IntelligenceResult(news_id=item.id, status="no_event")
            return IntelligenceResult(news_id=item.id, status="accepted_fallback", claim=normalize_claim_location(claim), reason="deterministic_fallback")

        return IntelligenceResult(news_id=item.id, status="accepted", claim=normalize_claim_location(claim))
