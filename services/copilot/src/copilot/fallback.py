"""Rule-based fallback responses (design.md §6.4).

Used whenever the retrieval context is empty, stale, or OOD-flagged
(`rule_based_response`) — or, as an extension not explicitly spelled out in
§6.4 but implied by its "never answer ungrounded" intent, whenever the LLM
path itself fails (`llm_unavailable_response`). Either way the copilot never
returns an LLM-shaped answer without a working, grounded LLM call behind it.
"""

from typing import Any


def rule_based_response(states: list[dict[str, Any]]) -> str:
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
        "The most recent sensor reading is more than 5 minutes old, so I don't have "
        "current enough data to answer confidently. Please check the sensor connection."
    )


def llm_unavailable_response() -> str:
    return (
        "I have current sensor data, but I'm temporarily unable to generate a "
        "natural-language explanation. Please check the dashboard directly for the "
        "current health index, vibration readings, and any active alerts."
    )
