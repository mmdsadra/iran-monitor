from dataclasses import dataclass
from pathlib import Path

from iran_monitor.events.model import Event
from iran_monitor.output.assessment import SituationAssessment, assess_events
from iran_monitor.output.render import render_assessment, render_map, render_pie
from iran_monitor.output.report import build_report


@dataclass(frozen=True)
class EventFeed:
    report: str
    map_path: Path
    assessment_path: Path
    pie_path: Path
    assessment: SituationAssessment


class IntelligenceFeedBuilder:
    """Build the complete Telegram-ready intelligence package."""

    def build(self, events: list[Event], output_dir: str | Path) -> EventFeed:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        assessment = assess_events(events)
        return EventFeed(
            report=build_report(events, assessment),
            map_path=render_map(events, output / "iran_monitor_map.jpg"),
            assessment_path=render_assessment(assessment, output / "iran_monitor_assessment.jpg"),
            pie_path=render_pie(assessment, output / "iran_monitor_pie.jpg"),
            assessment=assessment,
        )
