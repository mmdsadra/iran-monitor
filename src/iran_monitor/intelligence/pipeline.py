from iran_monitor.events.model import Event
from iran_monitor.intelligence.extractor import IntelligenceProvider
from iran_monitor.intelligence.gate import IntelligenceGate
from iran_monitor.models.news import NewsItem


class IntelligencePipeline:
    def __init__(
        self,
        gate: IntelligenceGate,
        provider: IntelligenceProvider,
    ):
        self.gate = gate
        self.provider = provider

    def process(self, items: list[NewsItem]) -> list[Event]:
        accepted, _ = self.gate.filter(items)

        events: list[Event] = []

        for item in accepted:
            event = self.provider.analyze(item)

            if event is not None:
                events.append(event)

        return events
