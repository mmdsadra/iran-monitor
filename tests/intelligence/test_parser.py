import pytest

from iran_monitor.events.model import EventType
from iran_monitor.intelligence.parser import (
    InvalidLLMResponse,
    parse_event_claim,
)


def test_parse_valid_claim():
    response = """
    {
        "event_type": "explosion",
        "description": "Explosion reportedly heard.",
        "location_text": "Isfahan",
        "country": "Iran",
        "city": "Isfahan",
        "occurred_at": null,
        "confidence": 0.8,
        "evidence_text": "Source reported an explosion."
    }
    """

    claim = parse_event_claim(response)

    assert claim is not None
    assert claim.event_type == EventType.EXPLOSION
    assert claim.city == "Isfahan"
    assert claim.confidence == 0.8


def test_parse_null():
    assert parse_event_claim("null") is None


def test_invalid_json_is_rejected():
    with pytest.raises(InvalidLLMResponse):
        parse_event_claim("this is not json")


def test_invalid_confidence_is_rejected():
    response = """
    {
        "event_type": "explosion",
        "description": "Explosion",
        "confidence": 2.5
    }
    """

    with pytest.raises(InvalidLLMResponse):
        parse_event_claim(response)


def test_array_is_rejected():
    with pytest.raises(InvalidLLMResponse):
        parse_event_claim("[]")
