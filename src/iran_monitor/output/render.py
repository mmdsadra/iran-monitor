from pathlib import Path
from typing import Iterable

from iran_monitor.events.model import Event
from iran_monitor.intelligence.geography import resolve_place
from iran_monitor.output.assessment import SituationAssessment


NATURAL_EARTH_COUNTRIES = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_50m_admin_0_countries.geojson"
)

FALLBACK_CITIES = {
    "tehran": (51.389, 35.689),
    "isfahan": (51.668, 32.655),
    "bandar abbas": (56.267, 27.183),
    "sirik": (57.529, 27.115),
    "strait of hormuz": (56.25, 26.567),
}


def _event_coordinates(event: Event) -> tuple[float, float] | None:
    if event.latitude is not None and event.longitude is not None:
        return event.longitude, event.latitude

    place = resolve_place(event.city, event.location_text, event.description)
    if place is not None:
        return place.longitude, place.latitude

    text = " ".join(v.strip().lower() for v in [event.city or "", event.location_text or ""] if v)
    for name, coords in FALLBACK_CITIES.items():
        if name in text:
            return coords
    return None


def _load_real_basemap():
    import geopandas as gpd

    world = gpd.read_file(NATURAL_EARTH_COUNTRIES)
    return world.cx[25:75, 10:45]


def render_map(events: Iterable[Event], output_path: str | Path) -> Path:
    """Render a real Natural Earth country-boundary map with event markers."""
    import matplotlib.pyplot as plt

    events = list(events)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 9))

    try:
        world = _load_real_basemap()
        world.boundary.plot(ax=ax, linewidth=0.55)
        iran = world[world["ADMIN"].astype(str).str.lower().eq("iran")]
        if not iran.empty:
            iran.plot(ax=ax, alpha=0.08)
            iran.boundary.plot(ax=ax, linewidth=1.6)
        ax.set_xlim(25, 75)
        ax.set_ylim(10, 45)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("Iran Monitor — Middle East Event Map")
        ax.grid(True, alpha=0.12)
        basemap_ok = True
    except Exception:
        ax.set_xlim(25, 75)
        ax.set_ylim(10, 45)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.12)
        ax.set_title("Iran Monitor — Event Map (fallback)")
        basemap_ok = False

    plotted = 0
    for event in events:
        coords = _event_coordinates(event)
        if coords is None:
            continue
        longitude, latitude = coords
        if not (25 <= longitude <= 75 and 10 <= latitude <= 45):
            continue
        size = 35 + 220 * max(0.0, min(1.0, event.severity))
        ax.scatter(longitude, latitude, s=size, alpha=0.82, zorder=5)
        label = event.city or event.location_text or event.event_type.value
        ax.annotate(label, (longitude, latitude), xytext=(5, 5), textcoords="offset points", fontsize=7, zorder=6)
        plotted += 1

    if plotted == 0:
        ax.text(50, 27, "No geolocated events yet", ha="center", fontsize=12)

    source_note = "Natural Earth 50m country boundaries" if basemap_ok else "Fallback map — Natural Earth unavailable"
    ax.text(0.01, 0.01, f"Events plotted: {plotted} | {source_note}", transform=ax.transAxes, fontsize=7, alpha=0.65)
    fig.tight_layout()
    fig.savefig(path, format="jpg", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def render_assessment(assessment: SituationAssessment, output_path: str | Path) -> Path:
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
    import matplotlib.pyplot as plt

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = ["War", "Diplomacy", "Protests", "Military", "Infrastructure", "Casualties"]
    values = [assessment.war, assessment.diplomacy, assessment.protests, assessment.military, assessment.infrastructure, assessment.casualties]
    if sum(values) == 0:
        labels, values = ["No signal"], [1]
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
    ax.set_title("Iran Monitor — Situation Signal Mix")
    fig.tight_layout()
    fig.savefig(path, format="jpg", dpi=150)
    plt.close(fig)
    return path
