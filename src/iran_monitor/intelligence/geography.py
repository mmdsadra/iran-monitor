from __future__ import annotations

from dataclasses import dataclass

from iran_monitor.intelligence.claims import EventClaim


@dataclass(frozen=True)
class Place:
    country: str
    city: str | None
    latitude: float
    longitude: float


# Curated locations used only when the source explicitly names the place.
# Coordinates are deterministic and do not come from the LLM.
PLACES: dict[str, Place] = {
    "tehran": Place("Iran", "Tehran", 35.6892, 51.3890),
    "تهران": Place("Iran", "Tehran", 35.6892, 51.3890),
    "isfahan": Place("Iran", "Isfahan", 32.6546, 51.6680),
    "اصفهان": Place("Iran", "Isfahan", 32.6546, 51.6680),
    "اصفان": Place("Iran", "Isfahan", 32.6546, 51.6680),
    "shiraz": Place("Iran", "Shiraz", 29.5918, 52.5837),
    "شیراز": Place("Iran", "Shiraz", 29.5918, 52.5837),
    "tabriz": Place("Iran", "Tabriz", 38.0962, 46.2738),
    "تبریز": Place("Iran", "Tabriz", 38.0962, 46.2738),
    "mashhad": Place("Iran", "Mashhad", 36.2605, 59.6168),
    "مشهد": Place("Iran", "Mashhad", 36.2605, 59.6168),
    "ahvaz": Place("Iran", "Ahvaz", 31.3183, 48.6706),
    "اهواز": Place("Iran", "Ahvaz", 31.3183, 48.6706),
    "bandar abbas": Place("Iran", "Bandar Abbas", 27.1832, 56.2666),
    "bandarabbas": Place("Iran", "Bandar Abbas", 27.1832, 56.2666),
    "بندرعباس": Place("Iran", "Bandar Abbas", 27.1832, 56.2666),
    "sirik": Place("Iran", "Sirik", 27.1147, 57.5294),
    "sirīk": Place("Iran", "Sirik", 27.1147, 57.5294),
    "سیریک": Place("Iran", "Sirik", 27.1147, 57.5294),
    "hormuz": Place("Iran", "Hormuz", 27.0587, 56.4650),
    "تنگه هرمز": Place("Iran", "Strait of Hormuz", 26.5667, 56.2500),
    "strait of hormuz": Place("Iran", "Strait of Hormuz", 26.5667, 56.2500),
    "persian gulf": Place("Iran", "Persian Gulf", 26.0000, 52.0000),
    "خلیج فارس": Place("Iran", "Persian Gulf", 26.0000, 52.0000),
    "red sea": Place("Egypt", "Red Sea", 20.5000, 38.5000),
    "دریای سرخ": Place("Egypt", "Red Sea", 20.5000, 38.5000),
    "baghdad": Place("Iraq", "Baghdad", 33.3152, 44.3661),
    "بغداد": Place("Iraq", "Baghdad", 33.3152, 44.3661),
    "erbil": Place("Iraq", "Erbil", 36.1911, 44.0092),
    "اربیل": Place("Iraq", "Erbil", 36.1911, 44.0092),
    "doha": Place("Qatar", "Doha", 25.2854, 51.5310),
    "دبی": Place("United Arab Emirates", "Dubai", 25.2048, 55.2708),
    "dubai": Place("United Arab Emirates", "Dubai", 25.2048, 55.2708),
    "riyadh": Place("Saudi Arabia", "Riyadh", 24.7136, 46.6753),
    "ریاض": Place("Saudi Arabia", "Riyadh", 24.7136, 46.6753),
    "tel aviv": Place("Israel", "Tel Aviv", 32.0853, 34.7818),
    "تل آویو": Place("Israel", "Tel Aviv", 32.0853, 34.7818),
    "jerusalem": Place("Israel", "Jerusalem", 31.7683, 35.2137),
    "اورشلیم": Place("Israel", "Jerusalem", 31.7683, 35.2137),
}


def resolve_place(*values: str | None) -> Place | None:
    text = " ".join(value.strip().lower() for value in values if value and value.strip())
    if not text:
        return None

    # Longest aliases first prevents a generic substring from winning.
    for alias in sorted(PLACES, key=len, reverse=True):
        if alias in text:
            return PLACES[alias]
    return None


def normalize_claim_location(claim: EventClaim) -> EventClaim:
    """Fill canonical country/city when the source text explicitly names a known place."""
    place = resolve_place(claim.city, claim.location_text, claim.description)
    if place is None:
        return claim

    return claim.model_copy(
        update={
            "country": claim.country or place.country,
            "city": claim.city or place.city,
        }
    )
