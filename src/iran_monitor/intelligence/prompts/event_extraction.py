from iran_monitor.models.news import NewsItem


SYSTEM_PROMPT = """
You are an intelligence event extraction system.

Extract a meaningful factual event from the supplied news report.

Rules:
- Prefer extracting an event when the report describes a concrete real-world event.
- Do not invent facts.
- Do not infer a location unless supported by the text.
- Do not treat speculation, predictions, or allegations as confirmed facts.
- Confidence measures confidence that the extracted event is actually described by the source, not event severity.
- Use event_type=other for a meaningful event that does not fit another type.
- Return null only when the report contains no meaningful real-world event.
- Return ONLY valid JSON. Do not use Markdown fences. Do not add commentary.
- occurred_at may be null when the time is unknown.
- country and city may be null when unsupported.
- confidence must be a number from 0.0 to 1.0.

Allowed event_type values:
explosion, fire, strike, attack, protest, military_movement,
airstrike, missile_launch, infrastructure_damage, casualty, other
"""


def build_event_extraction_prompt(item: NewsItem) -> str:
    title = item.title or ""
    text = item.text

    return f"""
Extract the main factual event from this news item.

SOURCE:
{item.source_name}

LANGUAGE:
{item.language}

TITLE:
{title}

TEXT:
{text}

Return exactly one JSON object with these fields:
{{
  "event_type": "...",
  "description": "short factual description",
  "location_text": null,
  "country": null,
  "city": null,
  "occurred_at": null,
  "confidence": 0.0,
  "evidence_text": "short quote or faithful excerpt supporting the event"
}}

If and only if there is no meaningful real-world event, return:
null
"""
