import re

from iran_monitor.models.news import NewsItem
from iran_monitor.intelligence.models import GateDecision, RejectionReason


GAMBLING_PATTERNS = [
    r"\bcasino\b", r"\bbet\b", r"\bbetting\b", r"\bsportsbook\b",
    r"\bpoker\b", r"\broulette\b", r"\bjackpot\b", r"\bslot\b", r"\bslots\b",
    r"کازینو", r"قمار", r"شرط.?بندی", r"پوکر", r"رولت", r"جک.?پات", r"کسب درآمد با بازی",
]

ADVERTISEMENT_PATTERNS = [
    r"همین الان", r"ثبت نام کن", r"ثبت.?نام", r"کد تخفیف", r"تخفیف ویژه",
    r"فرصت محدود", r"هدیه ویژه", r"درآمد میلیونی", r"واریز کن", r"شارژ کن", r"جایزه نقدی",
]

# High-confidence Iranian entities and locations. These deliberately include
# Persian/English spellings and strategic geography around Iran.
IRAN_PATTERNS = [
    r"\biran\b", r"\birgc\b", r"\bislamic republic of iran\b", r"\biranian\b",
    r"ایران", r"ایرانی", r"جمهوری اسلامی", r"سپاه پاسداران", r"سپاه", r"ارتش ایران",
    r"\btehran\b", r"\bتهران\b", r"\btabriz\b", r"\bتبریز\b", r"\bisfahan\b", r"\bاصفهان\b",
    r"\bshiraz\b", r"\bشیراز\b", r"\bbandar abbas\b", r"\bبندرعباس\b", r"\bsirik\b", r"\bسیریک\b",
    r"\bbushehr\b", r"\bبوشهر\b", r"\bkhuzestan\b", r"\bخوزستان\b", r"\bpersian gulf\b", r"\bخلیج فارس\b",
    r"\bstrait of hormuz\b", r"\bhormuz\b", r"\bتنگه هرمز\b", r"\bهرمز\b",
    r"\bnatanz\b", r"\bfordow\b", r"\bفردو\b", r"\bnuclear sites? in iran\b",
]

# Regional actors/contexts that can materially affect Iran even without the
# word Iran appearing in a headline.
REGIONAL_CONTEXT_PATTERNS = [
    r"\bisrael\b", r"\bisraeli\b", r"\bاسرائیل\b", r"\bاسراییل\b",
    r"\bunited states\b", r"\bus military\b", r"\bpentagon\b", r"\bآمریکا\b", r"\bپنتاگون\b",
    r"\biran.?us talks?\b", r"\bus.?iran talks?\b", r"\biran.?israel\b", r"\bisrael.?iran\b",
    r"\bhouthi\b", r"\bhouthi.?s\b", r"\bحوثی", r"\bred sea\b", r"\bدریای سرخ\b",
    r"\bcarrier strike group\b", r"\baircraft carrier\b", r"\bناو هواپیمابر\b",
    r"\bgulf of oman\b", r"\bدریای عمان\b", r"\barabian sea\b", r"\bدریای عرب\b",
]


def _matches(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def evaluate_rules(item: NewsItem) -> GateDecision:
    text = " ".join(part for part in [item.title or "", item.text] if part).strip()

    if not text:
        return GateDecision(accepted=False, reason=RejectionReason.SPAM, score=1.0)

    if _matches(text, GAMBLING_PATTERNS):
        return GateDecision(accepted=False, reason=RejectionReason.GAMBLING, score=0.99)

    if _matches(text, ADVERTISEMENT_PATTERNS):
        return GateDecision(accepted=False, reason=RejectionReason.ADVERTISEMENT, score=0.90)

    iran_hits = sum(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in IRAN_PATTERNS)
    regional_hits = sum(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in REGIONAL_CONTEXT_PATTERNS)

    # One explicit Iran entity is enough. Strategic regional stories need
    # at least two contextual signals, avoiding unrelated foreign incidents.
    if iran_hits:
        relevance = min(1.0, 0.75 + 0.08 * (iran_hits - 1))
        return GateDecision(accepted=True, score=1.0, relevance_score=relevance)

    if regional_hits >= 2:
        relevance = min(0.72, 0.45 + 0.10 * (regional_hits - 2))
        return GateDecision(accepted=True, score=1.0, relevance_score=relevance)

    return GateDecision(
        accepted=False,
        reason=RejectionReason.IRRELEVANT,
        score=0.95,
        relevance_score=0.0,
    )
