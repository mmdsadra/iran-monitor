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

IRAN_PATTERNS = [
    r"\biran\b", r"\birgc\b", r"\bislamic republic of iran\b", r"\biranian\b",
    r"ایران", r"ایرانی", r"جمهوری اسلامی", r"سپاه پاسداران", r"سپاه", r"ارتش ایران",
    r"\btehran\b", r"\bتهران\b", r"\btabriz\b", r"\bتبریز\b", r"\bisfahan\b", r"\bاصفهان\b",
    r"\bshiraz\b", r"\bشیراز\b", r"\bbandar abbas\b", r"\bبندرعباس\b", r"\bsirik\b", r"\bسیریک\b",
    r"\bbushehr\b", r"\bبوشهر\b", r"\bkhuzestan\b", r"\bخوزستان\b", r"\bpersian gulf\b", r"\bخلیج فارس\b",
    r"\bstrait of hormuz\b", r"\bhormuz\b", r"\bتنگه هرمز\b", r"\bهرمز\b",
    r"\bnatanz\b", r"\bfordow\b", r"\bفردو\b", r"\bnuclear sites? in iran\b",
]

REGIONAL_CONTEXT_PATTERNS = [
    r"\bisrael\b", r"\bisraeli\b", r"\bاسرائیل\b", r"\bاسراییل\b",
    r"\bunited states\b", r"\bus military\b", r"\bpentagon\b", r"\bآمریکا\b", r"\bپنتاگون\b",
    r"\biran.?us talks?\b", r"\bus.?iran talks?\b", r"\biran.?israel\b", r"\bisrael.?iran\b",
    r"\bhouthi\b", r"\bhouthi.?s\b", r"\bحوثی", r"\bred sea\b", r"\bدریای سرخ\b",
    r"\bcarrier strike group\b", r"\baircraft carrier\b", r"\bناو هواپیمابر\b",
    r"\bgulf of oman\b", r"\bدریای عمان\b", r"\barabian sea\b", r"\bدریای عرب\b",
]

PERSIAN_LOCAL_EVENT_PATTERNS = [
    r"انفجار", r"حمله", r"درگیری", r"شلیک", r"اصابت", r"موشک", r"پهپاد", r"رزمایش",
    r"آتش.?سوزی", r"تیراندازی", r"اعتراض", r"بازداشت", r"کشته", r"زخمی", r"تلفات",
    r"پایگاه", r"تأسیسات", r"تاسیسات", r"مرکز صنعتی", r"فرودگاه", r"بندر", r"استان",
    r"نیروهای مسلح", r"نیروی هوایی", r"نیروی دریایی", r"ارتش", r"سپاه",
]

# Common Iran-focused Persian news vocabulary. These are intentionally
# broader than physical-location keywords because Telegram alerts about
# diplomacy, protests, politics and the economy often contain no city name.
PERSIAN_IRAN_TOPIC_PATTERNS = [
    r"مذاکر(?:ه|ات)", r"دیپلماسی", r"تحریم", r"تحریم.?ها", r"برجام", r"هسته.?ای",
    r"دولت", r"رئیس.?جمهور", r"ریاست.?جمهوری", r"وزارت", r"مجلس", r"نماینده",
    r"اعتراض(?:ات)?", r"تجمع", r"اعتصاب", r"معیشت", r"اقتصاد", r"تورم", r"ارز", r"دلار",
    r"انتخابات", r"رأی.?گیری", r"قوه قضائیه", r"دادگستری", r"بازداشت", r"زندانی",
    r"سپاه", r"ارتش", r"نیروی هوایی", r"نیروی دریایی", r"پدافند", r"موشک", r"پهپاد",
    r"نفت", r"گاز", r"پتروشیمی", r"برق", r"آب", r"سوخت", r"بنزین", r"خودرو",
    r"دانشگاه", r"دانشجو", r"معلم", r"کارگر", r"بازنشسته", r"خبرگزاری", r"وزیر",
]


def _matches(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _count_matches(text: str, patterns: list[str]) -> int:
    return sum(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in patterns)


def evaluate_rules(item: NewsItem) -> GateDecision:
    text = " ".join(part for part in [item.title or "", item.text] if part).strip()

    if not text:
        return GateDecision(accepted=False, reason=RejectionReason.SPAM, score=1.0)

    if _matches(text, GAMBLING_PATTERNS):
        return GateDecision(accepted=False, reason=RejectionReason.GAMBLING, score=0.99)

    if _matches(text, ADVERTISEMENT_PATTERNS):
        return GateDecision(accepted=False, reason=RejectionReason.ADVERTISEMENT, score=0.90)

    iran_hits = _count_matches(text, IRAN_PATTERNS)
    regional_hits = _count_matches(text, REGIONAL_CONTEXT_PATTERNS)

    if iran_hits:
        relevance = min(1.0, 0.75 + 0.08 * (iran_hits - 1))
        return GateDecision(accepted=True, score=1.0, relevance_score=relevance)

    if regional_hits >= 2:
        relevance = min(0.72, 0.45 + 0.10 * (regional_hits - 2))
        return GateDecision(accepted=True, score=1.0, relevance_score=relevance)

    # Curated Persian Telegram channels are important primary inputs for
    # Iran Monitor. Their alerts frequently omit "Iran" and city names,
    # especially for diplomacy, protests, domestic politics and economic
    # news. Accept those only when there is an Iran-specific topic signal;
    # unrelated English/foreign stories still fail the gate.
    is_persian = bool(re.search(r"[\u0600-\u06ff]", text)) and (
        (item.language or "").lower() in {"fa", "fas", "per"}
    )
    local_event_hits = _count_matches(text, PERSIAN_LOCAL_EVENT_PATTERNS)
    topic_hits = _count_matches(text, PERSIAN_IRAN_TOPIC_PATTERNS)
    if item.source_type.lower() == "telegram" and is_persian:
        if local_event_hits >= 1 or topic_hits >= 1:
            relevance = min(0.70, 0.45 + 0.08 * max(local_event_hits, topic_hits))
            return GateDecision(accepted=True, score=0.75, relevance_score=relevance)

    return GateDecision(
        accepted=False,
        reason=RejectionReason.IRRELEVANT,
        score=0.95,
        relevance_score=0.0,
    )
