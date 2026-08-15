"""System prompt + retrieved-context serialization (design.md §6.4)."""

from typing import Any

SYSTEM_PROMPT = (
    "You are the Digital Cousin copilot for a single monitored machine. Answer only "
    "questions about the machine's current health, recent anomalies, and active alerts, "
    "using ONLY the sensor state data provided in the user message. Never answer a question "
    "that isn't grounded in that data, and never provide maintenance instructions or safety "
    "guidance beyond what the data itself shows. If the data doesn't contain the answer, say "
    "so explicitly rather than guessing."
)


def format_context(states: list[dict[str, Any]]) -> str:
    """Serializes retrieved state objects (most-recent-first) into the
    structured context block injected into the prompt (design.md §6.4:
    "serialized and injected into the prompt as structured context").
    """
    lines = []
    for state in states:
        vibration = state.get("vibration") or {}
        lines.append(
            f"- {state.get('timestamp')}: health_index={state.get('health_index')}, "
            f"anomaly_score={state.get('anomaly_score')}, "
            f"alert_level={state.get('alert_level')}, "
            f"vibration_rms_g={vibration.get('rms_g')}, "
            f"kurtosis={vibration.get('kurtosis')}, "
            f"temperature_c={state.get('temperature_c')}"
        )
    return "\n".join(lines)


def build_user_prompt(query: str, states: list[dict[str, Any]]) -> str:
    return (
        f"Sensor state history (most recent first):\n{format_context(states)}\n\n"
        f"Operator question: {query}"
    )
