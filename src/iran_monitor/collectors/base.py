from abc import ABC, abstractmethod

from iran_monitor.models.news import NewsItem


class BaseCollector(ABC):
    """Base interface for all news collectors."""

    @abstractmethod
    def collect(self) -> list[NewsItem]:
        """Collect and normalize news items."""
        raise NotImplementedError
