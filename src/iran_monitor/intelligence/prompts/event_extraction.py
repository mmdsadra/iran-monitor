from iran_monitor.models.news import NewsItem


SYSTEM_PROMPT = """
You are an intelligence event extraction system.

Your job is to extract factual event claims from news reports.

Rules:
- Do not invent facts.
- Do not infer a location unless supported by the text.
- Do not treat speculation as confirmed fact.
- Confidence must represent confidence in the extracted claim, not the severity of the event.
- If there is no meaningful event, return null.
- Return only structured JSON matching the requested schema.
"""


def build_event_extraction_prompt(item: NewsItem) -> str:
    title = item.title or ""
    text = item.text

    return f"""
Extract a structured event claim from this news item.

SOURCE:
{item.source_name}

LANGUAGE:
{item.language}

TITLE:
{title}

TEXT:
{text}

Return either null or an object with:

event_type
description
location_text
country
city
occurred_at
confidence
evidence_text

Do not add fields outside this schema.
"""
