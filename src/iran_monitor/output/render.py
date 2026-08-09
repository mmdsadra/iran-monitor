from pathlib import Path
from typing import Iterable

from iran_monitor.events.model import Event
from iran_monitor.output.assessment import SituationAssessment


def render_map(events: Iterable[Event], output_path: str | Path) -> Path:
    """Render a lightweight JPG event map without external map tiles."""
    import matplotlib.pyplot as plt

    events = list(events)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(44, 64)
    ax.set_ylim(24, 40)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Iran Monitor — Event Map")
    ax.grid(True, alpha=0.25)

    plotted = 0
    for event in events:
        if event.latitude is None or event.longitude is None:
            continue
        ax.scatter(event.longitude, event.latitude, s=35 + 90 * event.severity, alpha=0.75)
        ax.annotate(event.city or event.event_type.value, (event.longitude, event.latitude), fontsize=8)
        plotted += 1

    if plotted == 0:
        ax.text(54, 32, "No geolocated events", ha="center", va="center")

    fig.tight_layout()
    fig.savefig(path, format="jpg", dpi=150)
    plt.close(fig)
    return path


def render_assessment(assessment: SituationAssessment, output_path: str | Path) -> Path:
    """Render the situation indicators as a JPG dashboard."""
    import matplotlib.pyplot as plt

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = ["War", "Diplomacy", "Protests", "Military", "Infrastructure", "Casualties"]
    values = [assessment.war, assessment.diplomacy, assessment.protests, assessment.military, assessment.infrastructure, assessment.casualties]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Indicator (0–100)")
    ax.set_title(f"Iran Monitor — Situation Indicators | Overall: {assessment.overall:.0f}/100")
    ax.grid(axis="y", alpha=0.25)
    for i, value in enumerate(values):
        ax.text(i, value + 2, f"{value:.0f}%", ha="center")
    fig.tight_layout()
    fig.savefig(path, format="jpg", dpi=150)
    plt.close(fig)
    return path


def render_pie(assessment: SituationAssessment, output_path: str | Path) -> Path:
    """Render a JPG pie chart of the current event-pressure composition."""
    import matplotlib.pyplot as plt

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = ["War", "Diplomacy", "Protests", "Military", "Infrastructure", "Casualties"]
    values = [assessment.war, assessment.diplomacy, assessment.protests, assessment.military, assessment.infrastructure, assessment.casualties]
    total = sum(values)
    if total == 0:
        labels, values = ["No signal"], [1]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
    ax.set_title("Iran Monitor — Situation Signal Mix")
    fig.tight_layout()
    fig.savefig(path, format="jpg", dpi=150)
    plt.close(fig)
    return path
