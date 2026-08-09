import re

from iran_monitor.classification.models import (
    ClassificationResult,
    EventCategory,
    EventType,
)
from iran_monitor.models.news import NewsItem


RULES = [
    (
        EventCategory.SECURITY,
        EventType.EXPLOSION,
        [r"انفجار", r"\bexplosion\b", r"\bblast\b"],
    ),
    (
        EventCategory.SECURITY,
        EventType.MISSILE,
        [r"موشک", r"\bmissile\b"],
    ),
    (
        EventCategory.SECURITY,
        EventType.DRONE,
        [r"پهپاد", r"\bdrone\b", r"\buav\b"],
    ),
    (
        EventCategory.SECURITY,
        EventType.AIRSTRIKE,
        [r"حمله هوایی", r"حمله هوایی", r"\bairstrike\b"],
    ),
    (
        EventCategory.SECURITY,
        EventType.MILITARY_MOVEMENT,
        [r"تحرکات نظامی", r"نیروهای نظامی", r"\bmilitary movement\b"],
    ),
    (
        EventCategory.POLITICAL,
        EventType.NEGOTIATION,
        [r"مذاکره", r"مذاکرات", r"\bnegotiation\b", r"\btalks\b"],
    ),
    (
        EventCategory.POLITICAL,
        EventType.GOVERNMENT_STATEMENT,
        [r"رئیس.?جمهور", r"وزیر", r"سخنگو", r"\bgovernment statement\b"],
    ),
    (
        EventCategory.POLITICAL,
        EventType.DIPLOMATIC_EVENT,
        [r"دیپلمات", r"دیپلماتیک", r"\bdiplomatic\b"],
    ),
    (
        EventCategory.CIVIL,
        EventType.PROTEST,
        [r"اعتراض", r"اعتراضات", r"\bprotest\b"],
    ),
    (
        EventCategory.CIVIL,
        EventType.STRIKE,
        [r"اعتصاب", r"\bstrike\b"],
    ),
    (
        EventCategory.CIVIL,
        EventType.ROAD_CLOSURE,
        [r"مسدود شدن جاده", r"انسداد جاده", r"\broad closure\b"],
    ),
    (
        EventCategory.INFRASTRUCTURE,
        EventType.FIRE,
        [r"آتش.?سوزی", r"\bfire\b"],
    ),
    (
        EventCategory.INFRASTRUCTURE,
        EventType.PORT,
        [r"بندر", r"\bport\b"],
    ),
    (
        EventCategory.INFRASTRUCTURE,
        EventType.AIRPORT,
        [r"فرودگاه", r"\bairport\b"],
    ),
    (
        EventCategory.INFRASTRUCTURE,
        EventType.FUEL_STATION,
        [r"پمپ بنزین", r"جایگاه سوخت", r"\bfuel station\b"],
    ),
    (
        EventCategory.NATURAL_DISASTER,
        EventType.EARTHQUAKE,
        [r"زلزله", r"\bearthquake\b"],
    ),
]


def classify(item: NewsItem) -> ClassificationResult:
    text = " ".join(
        part for part in [item.title or "", item.text] if part
    )

    for category, event_type, patterns in RULES:
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            return ClassificationResult(
                category=category,
                event_type=event_type,
                confidence=0.90,
            )

    return ClassificationResult(
        category=EventCategory.OTHER,
        event_type=EventType.UNKNOWN,
        confidence=0.20,
    )
