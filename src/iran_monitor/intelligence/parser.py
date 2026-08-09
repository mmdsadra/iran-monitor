import json
import re

from pydantic import ValidationError

from iran_monitor.intelligence.claims import EventClaim


class InvalidLLMResponse(ValueError):
    """Raised when an LLM response cannot be safely validated."""


def _clean_json_response(response: str) -> str:
    response = response.strip()
    if response.startswith("```json") and response.endswith("```"):
        return response[7:-3].strip()
    if response.startswith("```") and response.endswith("```"):
        return response[3:-3].strip()

    match = re.search(r"(?:\{.*\}|null)", response, re.DOTALL)
    if match:
        return match.group(0).strip()
    return response


def parse_event_claim(response: str) -> EventClaim | None:
    response = _clean_json_response(response)

    if response.lower() == "null":
        return None

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise InvalidLLMResponse(
            f"LLM returned invalid JSON: {response[:500]}"
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
            f"LLM response failed schema validation: {exc}"
        ) from exc
