from iran_monitor.classification.models import ClassificationResult
from iran_monitor.classification.rules import classify
from iran_monitor.models.news import NewsItem


class EventClassifier:
    """Classify a normalized NewsItem into an event category/type."""

    def classify(self, item: NewsItem) -> ClassificationResult:
        return classify(item)
