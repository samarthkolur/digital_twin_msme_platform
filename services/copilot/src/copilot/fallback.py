"""Rule-based fallback responses (design.md §6.4).

Used whenever the retrieval context is empty, stale, or OOD-flagged
(`rule_based_response`) — or, as an extension not explicitly spelled out in
§6.4 but implied by its "never answer ungrounded" intent, whenever the LLM
path itself fails (`llm_unavailable_response`). Either way the copilot never
returns an LLM-shaped answer without a working, grounded LLM call behind it.
"""

from datetime import timedelta
from typing import Any

from copilot.context import STALE_AFTER

_SECONDS_PER_MINUTE = 60
_SECONDS_PER_HOUR = 3600


def _describe(window: timedelta) -> str:
    """5 minutes / 2 hours / 45 seconds — the largest whole unit that fits."""
    seconds = int(window.total_seconds())
    for unit_seconds, unit in ((_SECONDS_PER_HOUR, "hour"), (_SECONDS_PER_MINUTE, "minute")):
        if seconds % unit_seconds == 0:
            count = seconds // unit_seconds
            return f"{count} {unit}{'' if count == 1 else 's'}"
    return f"{seconds} second{'' if seconds == 1 else 's'}"


def rule_based_response(states: list[dict[str, Any]], stale_after: timedelta = STALE_AFTER) -> str:
    if not states:
        return (
            "I don't have any recent sensor data for this machine yet, so I can't answer "
            "that. Please check that the sensor kit is connected and reporting."
        )

    latest = states[0]
    if latest.get("model_confidence") == "low":
        return (
            "The most recent reading was flagged as low-confidence (values outside the "
            "range the anomaly model was trained on), so I can't give a reliable answer "
            "right now. Consider scheduling an inspection."
        )

    return (
        f"The most recent sensor reading is more than {_describe(stale_after)} old, so I "
        "don't have current enough data to answer confidently. Please check the sensor "
        "connection."
    )


def llm_unavailable_response() -> str:
    return (
        "I have current sensor data, but I'm temporarily unable to generate a "
        "natural-language explanation. Please check the dashboard directly for the "
        "current health index, vibration readings, and any active alerts."
    )
