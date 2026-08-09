from abc import ABC, abstractmethod

from iran_monitor.events.model import Event
from iran_monitor.models.news import NewsItem


class IntelligenceProvider(ABC):
    """Interface for extracting structured intelligence from news."""

    @abstractmethod
    def analyze(self, item: NewsItem) -> Event | None:
        """Analyze a NewsItem and return an Event if relevant."""
        raise NotImplementedError


class MockIntelligenceProvider(IntelligenceProvider):
    """
    Deterministic provider used for tests and local development.

    No external API calls.
    """

    def analyze(self, item: NewsItem) -> Event | None:
        return Event(
            id=f"event-{item.id}",
            event_type="other",
            title=item.title,
            description=item.text,
            location_text=None,
            country=None,
            city=None,
            latitude=None,
            longitude=None,
            occurred_at=item.published_at,
            confidence=0.0,
            source_ids=[item.id],
        )