from pathlib import Path
from typing import Iterable

from iran_monitor.events.model import Event
from iran_monitor.output.assessment import SituationAssessment


# Lightweight schematic geography so the project does not depend on map tiles,
# geopandas, or an external GIS service at runtime.
IRAN_OUTLINE = [
    (44.0, 39.7), (46.0, 38.9), (48.5, 39.3), (51.5, 38.1),
    (54.0, 37.2), (58.0, 37.0), (60.6, 36.7), (61.8, 34.2),
    (61.0, 31.0), (61.8, 27.2), (58.5, 25.3), (54.0, 25.2),
    (50.0, 26.0), (47.0, 28.0), (44.7, 30.0), (44.0, 33.0),
    (44.0, 39.7),
]

NEIGHBOR_OUTLINES = {
    "Turkey": [(44, 39.7), (38, 42), (35, 37), (44, 36), (44, 39.7)],
    "Iraq": [(44, 37), (48, 37), (48, 29.8), (44.7, 30), (44, 33), (44, 37)],
    "Azerbaijan": [(48, 39.3), (51.5, 38.1), (51, 41), (46.5, 41), (48, 39.3)],
    "Turkmenistan": [(58, 37), (60.6, 36.7), (62, 39), (66, 38), (66, 35), (61.8, 34.2), (58, 37)],
    "Afghanistan": [(61.8, 34.2), (66, 35), (70, 35), (72, 31), (66, 27), (61.8, 27.2), (61, 31), (61.8, 34.2)],
    "Pakistan": [(66, 27), (72, 31), (74, 28), (70, 24), (63, 24), (58.5, 25.3), (61.8, 27.2), (66, 27)],
    "Saudi Arabia": [(44.7, 30), (50, 26), (54, 25.2), (56, 22), (48, 17), (42, 20), (40, 25), (44.7, 30)],
}

CITY_COORDS = {
    "tehran": (51.389, 35.689), "تهران": (51.389, 35.689),
    "isfahan": (51.667, 32.654), "اصفهان": (51.667, 32.654), "اصفان": (51.667, 32.654),
    "shiraz": (52.531, 29.592), "شیراز": (52.531, 29.592),
    "tabriz": (46.291, 38.096), "تبریز": (46.291, 38.096),
    "mashhad": (59.606, 36.297), "مشهد": (59.606, 36.297),
    "ahvaz": (48.670, 31.318), "اهواز": (48.670, 31.318),
    "qom": (50.876, 34.641), "قم": (50.876, 34.641),
    "kermanshah": (47.065, 34.315), "کرمانشاه": (47.065, 34.315),
    "bandar abbas": (56.266, 27.183), "بندرعباس": (56.266, 27.183),
    "rasht": (49.583, 37.280), "رشت": (49.583, 37.280),
    "karaj": (50.992, 35.840), "کرج": (50.992, 35.840),
    "yazd": (54.367, 31.897), "یزد": (54.367, 31.897),
    "kurdistan": (46.0, 35.8), "کردستان": (46.0, 35.8),
}


def _event_coordinates(event: Event) -> tuple[float, float] | None:
    if event.latitude is not None and event.longitude is not None:
        return event.longitude, event.latitude

    text = " ".join(
        value.strip() for value in [event.city or "", event.location_text or ""] if value
    ).lower()
    for name, coords in CITY_COORDS.items():
        if name in text:
            return coords
    return None


def render_map(events: Iterable[Event], output_path: str | Path) -> Path:
    """Render a self-contained schematic Middle East map with event markers."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    events = list(events)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(38, 75)
    ax.set_ylim(17, 43)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Iran Monitor — Middle East Event Map")
    ax.grid(True, alpha=0.15)

    for name, outline in NEIGHBOR_OUTLINES.items():
        ax.add_patch(Polygon(outline, closed=True, fill=False, linewidth=0.8))
        center_x = sum(p[0] for p in outline) / len(outline)
        center_y = sum(p[1] for p in outline) / len(outline)
        ax.text(center_x, center_y, name, fontsize=7, ha="center", alpha=0.65)

    ax.add_patch(Polygon(IRAN_OUTLINE, closed=True, fill=False, linewidth=2.0))
    ax.text(54.0, 32.0, "IRAN", fontsize=14, fontweight="bold", ha="center", alpha=0.65)

    plotted = 0
    for event in events:
        coords = _event_coordinates(event)
        if coords is None:
            continue
        longitude, latitude = coords
        if not (38 <= longitude <= 75 and 17 <= latitude <= 43):
            continue
        ax.scatter(longitude, latitude, s=40 + 180 * event.severity, alpha=0.8)
        label = event.city or event.location_text or event.event_type.value
        ax.annotate(label, (longitude, latitude), xytext=(4, 4), textcoords="offset points", fontsize=7)
        plotted += 1

    if plotted == 0:
        ax.text(56.5, 29.0, "No geolocated events yet", ha="center", fontsize=11)

    ax.text(
        0.01, 0.01,
        f"Events plotted: {plotted} | Schematic geography; event positions are source-derived",
        transform=ax.transAxes, fontsize=7, alpha=0.6,
    )
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
