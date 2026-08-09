import hashlib
import re
from datetime import datetime, timezone

from iran_monitor.events.model import Event, EventType
from iran_monitor.models.news import NewsItem


class EventExtractor:
    """Deterministic event extractor.

    This is intentionally conservative:
    - irrelevant/news noise -> None
    - recognized event -> Event
    - ambiguous text -> OTHER with low confidence
    """

    EVENT_PATTERNS: dict[EventType, list[str]] = {
        EventType.EXPLOSION: [
            r"\bexplosion\b",
            r"\bexploded\b",
            r"انفجار",
            r"انفجاری",
        ],
        EventType.FIRE: [
            r"\bfire\b",
            r"\bburning\b",
            r"آتش.?سوزی",
            r"آتش گرفت",
            r"حریق",
        ],
        EventType.AIRSTRIKE: [
            r"\bairstrike\b",
            r"\bair strike\b",
            r"حمله هوایی",
            r"حملات هوایی",
            r"بمباران هوایی",
        ],
        EventType.MISSILE_LAUNCH: [
            r"\bmissile launch\b",
            r"\bmissile launched\b",
            r"پرتاب موشک",
            r"موشک شلیک",
            r"موشک پرتاب",
        ],
        EventType.STRIKE: [
            r"\bstrike\b",
            r"حمله موشکی",
            r"حمله به",
            r"مورد حمله قرار گرفت",
        ],
        EventType.ATTACK: [
            r"\battack\b",
            r"حمله",
            r"مورد حمله",
        ],
        EventType.PROTEST: [
            r"\bprotest\b",
            r"\bprotests\b",
            r"اعتراض",
            r"تجمع اعتراضی",
            r"تظاهرات",
        ],
        EventType.MILITARY_MOVEMENT: [
            r"\bmilitary movement\b",
            r"\bmilitary convoy\b",
            r"تحرک نظامی",
            r"کاروان نظامی",
            r"جابجایی نیرو",
        ],
        EventType.INFRASTRUCTURE_DAMAGE: [
            r"\binfrastructure damage\b",
            r"خسارت به زیرساخت",
            r"آسیب به زیرساخت",
            r"تخریب زیرساخت",
        ],
        EventType.CASUALTY: [
            r"\bcasualties\b",
            r"\bcasualty\b",
            r"کشته",
            r"مجروح",
            r"زخمی",
            r"تلفات",
        ],
    }

    def extract(self, item: NewsItem) -> Event | None:
        text = " ".join(
            part for part in [item.title or "", item.text] if part
        ).strip()

        if not text:
            return None

        event_type, confidence = self._classify(text)

        if event_type is None:
            return None

        return Event(
            id=self._make_event_id(item),
            event_type=event_type,
            title=item.title,
            description=item.text,
            location_text=self._extract_location(text),
            occurred_at=item.published_at,
            confidence=confidence,
            source_ids=[item.id],
        )

    def _classify(self, text: str) -> tuple[EventType | None, float]:
        matches: list[tuple[EventType, int]] = []

        for event_type, patterns in self.EVENT_PATTERNS.items():
            count = sum(
                1
                for pattern in patterns
                if re.search(pattern, text, re.IGNORECASE)
            )

            if count:
                matches.append((event_type, count))

        if not matches:
            return None, 0.0

        # Prefer the event type with the strongest evidence.
        matches.sort(key=lambda x: x[1], reverse=True)
        event_type, count = matches[0]

        confidence = min(0.60 + (count - 1) * 0.10, 0.90)

        return event_type, confidence

    @staticmethod
    def _extract_location(text: str) -> str | None:
        patterns = [
            r"(?:در|در شهر|در منطقه|در استان)\s+([آ-یA-Za-z][آ-یA-Za-z\s‌-]{2,40})",
            r"(?:in|near|at)\s+([A-Z][A-Za-z\s-]{2,40})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group(1).strip()
                location = re.split(
                    r"\s+(?:و|که|اما|در|با|به)\s+",
                    location,
                    maxsplit=1,
                )[0]
                return location.strip(" ،,.!?")

        return None

    @staticmethod
    def _make_event_id(item: NewsItem) -> str:
        raw = f"{item.source_name}:{item.id}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:24]
