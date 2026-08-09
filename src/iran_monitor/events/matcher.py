from dataclasses import dataclass
from datetime import datetime
import re

from iran_monitor.events.model import Event
from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.storage.events import EventRepository


@dataclass(frozen=True)
class EventMatch:
    event: Event
    score: float


class EventMatcher:
    """Deterministic Claim -> Event matcher for the first intelligence pass.

    Matching intentionally uses explainable signals rather than an embedding model:
    event type, geographic overlap, temporal proximity, and description tokens.
    """

    def __init__(
        self,
        repository: EventRepository,
        *,
        threshold: float = 0.65,
        time_window_hours: float = 12.0,
        candidate_limit: int = 100,
    ):
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if time_window_hours <= 0:
            raise ValueError("time_window_hours must be positive")
        if candidate_limit < 1:
            raise ValueError("candidate_limit must be positive")

        self.repository = repository
        self.threshold = threshold
        self.time_window_hours = time_window_hours
        self.candidate_limit = candidate_limit

    def find_match(self, claim: EventClaim) -> EventMatch | None:
        best: EventMatch | None = None

        for event in self.repository.list_recent(self.candidate_limit):
            score = self.score(claim, event)
            if score < self.threshold:
                continue
            if best is None or score > best.score:
                best = EventMatch(event=event, score=score)

        return best

    def score(self, claim: EventClaim, event: Event) -> float:
        if claim.event_type != event.event_type:
            return 0.0

        score = 0.50  # exact event type

        geo = self._geographic_score(claim, event)
        time = self._temporal_score(claim.occurred_at, event.occurred_at)
        text = self._text_score(claim.description, event.description)

        score += 0.20 * geo
        score += 0.20 * time
        score += 0.10 * text
        return min(score, 1.0)

    def _geographic_score(self, claim: EventClaim, event: Event) -> float:
        claim_city = self._normalize(claim.city)
        event_city = self._normalize(event.city)
        if claim_city and event_city:
            return 1.0 if claim_city == event_city else 0.0

        claim_country = self._normalize(claim.country)
        event_country = self._normalize(event.country)
        if claim_country and event_country:
            return 1.0 if claim_country == event_country else 0.0

        claim_location = self._normalize(claim.location_text)
        event_location = self._normalize(event.location_text)
        if claim_location and event_location:
            return 1.0 if claim_location in event_location or event_location in claim_location else 0.0

        return 0.0

    def _temporal_score(
        self,
        claim_time: datetime | None,
        event_time: datetime | None,
    ) -> float:
        if claim_time is None or event_time is None:
            return 0.0

        claim_time = self._aware_utc(claim_time)
        event_time = self._aware_utc(event_time)
        hours = abs((claim_time - event_time).total_seconds()) / 3600.0
        if hours > self.time_window_hours:
            return 0.0
        return 1.0 - (hours / self.time_window_hours)

    @staticmethod
    def _text_score(left: str, right: str) -> float:
        left_tokens = EventMatcher._tokens(left)
        right_tokens = EventMatcher._tokens(right)
        if not left_tokens or not right_tokens:
            return 0.0
        intersection = left_tokens & right_tokens
        union = left_tokens | right_tokens
        return len(intersection) / len(union)

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[\w\u0600-\u06ff]+", value.lower())
            if len(token) > 2
        }

    @staticmethod
    def _normalize(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.lower().split())
        return normalized or None

    @staticmethod
    def _aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(__import__("datetime").timezone.utc).replace(tzinfo=None)
