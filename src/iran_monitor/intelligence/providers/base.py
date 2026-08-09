from abc import ABC, abstractmethod

from iran_monitor.events.model import Event
from iran_monitor.models.news import NewsItem


class LLMProvider(ABC):
    """Provider interface for structured intelligence extraction."""

    @abstractmethod
    def analyze(self, item: NewsItem) -> Event | None:
        raise NotImplementedError
