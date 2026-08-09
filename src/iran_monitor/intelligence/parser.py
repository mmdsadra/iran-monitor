import json

from pydantic import ValidationError

from iran_monitor.intelligence.claims import EventClaim


class InvalidLLMResponse(ValueError):
    """Raised when an LLM response cannot be safely validated."""


def parse_event_claim(response: str) -> EventClaim | None:
    response = response.strip()

    if response == "null":
        return None

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise InvalidLLMResponse(
            "LLM returned invalid JSON"
        ) from exc

    if data is None:
        return None

    if not isinstance(data, dict):
        raise InvalidLLMResponse(
            "LLM response must be a JSON object or null"
        )

    try:
        return EventClaim.model_validate(data)
    except ValidationError as exc:
        raise InvalidLLMResponse(
            "LLM response failed schema validation"
        ) from exc
