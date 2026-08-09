import re

from iran_monitor.models.news import NewsItem
from iran_monitor.intelligence.models import GateDecision, RejectionReason


GAMBLING_PATTERNS = [
    r"\bcasino\b",
    r"\bbet\b",
    r"\bbetting\b",
    r"\bsportsbook\b",
    r"\bpoker\b",
    r"\broulette\b",
    r"\bjackpot\b",
    r"\bslot\b",
    r"\bslots\b",
    r"کازینو",
    r"قمار",
    r"شرط.?بندی",
    r"پوکر",
    r"رولت",
    r"جک.?پات",
    r"کسب درآمد با بازی",
]

ADVERTISEMENT_PATTERNS = [
    r"همین الان",
    r"ثبت نام کن",
    r"ثبت.?نام",
    r"کد تخفیف",
    r"تخفیف ویژه",
    r"فرصت محدود",
    r"هدیه ویژه",
    r"درآمد میلیونی",
    r"واریز کن",
    r"شارژ کن",
    r"جایزه نقدی",
]


def _matches(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def evaluate_rules(item: NewsItem) -> GateDecision:
    text = " ".join(
        part for part in [item.title or "", item.text] if part
    ).strip()

    if not text:
        return GateDecision(
            accepted=False,
            reason=RejectionReason.SPAM,
            score=1.0,
        )

    gambling = _matches(text, GAMBLING_PATTERNS)

    if gambling:
        return GateDecision(
            accepted=False,
            reason=RejectionReason.GAMBLING,
            score=0.99,
        )

    advertisement = _matches(text, ADVERTISEMENT_PATTERNS)

    if advertisement:
        return GateDecision(
            accepted=False,
            reason=RejectionReason.ADVERTISEMENT,
            score=0.90,
        )

    return GateDecision(
        accepted=True,
        score=1.0,
    )
