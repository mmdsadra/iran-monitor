from iran_monitor.models.news import NewsItem
from iran_monitor.intelligence.models import GateDecision
from iran_monitor.intelligence.rules import evaluate_rules


class IntelligenceGate:
    """First-pass filter before expensive intelligence processing."""

    def evaluate(self, item: NewsItem) -> GateDecision:
        return evaluate_rules(item)

    def filter(self, items: list[NewsItem]) -> tuple[list[NewsItem], list[GateDecision]]:
        accepted: list[NewsItem] = []
        rejected: list[GateDecision] = []

        for item in items:
            decision = self.evaluate(item)

            if decision.accepted:
                accepted.append(item)
            else:
                rejected.append(decision)

        return accepted, rejected
