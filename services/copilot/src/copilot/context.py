"""Retrieval-context validity checks (design.md §6.4).

"If the context is empty, stale (>5 minutes old), or flagged OOD, a
rule-based fallback response is returned instead of an LLM-generated
answer."
"""

from datetime import UTC, datetime, timedelta
from typing import Any

STALE_AFTER = timedelta(minutes=5)


def context_is_valid(states: list[dict[str, Any]]) -> bool:
    """`states` is most-recent-first (design.md §6.4's retrieval order,
    `retrieval.retrieve_recent_states`) — only the newest reading's
    freshness/confidence gates validity; older readings in the window are
    still passed to the LLM as historical context once the newest is valid.
    """
    if not states:
        return False

    latest = states[0]
    if latest.get("model_confidence") == "low":
        return False

    timestamp_raw = latest.get("timestamp")
    if not isinstance(timestamp_raw, str):
        return False
    try:
        timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
    except ValueError:
        return False

    return datetime.now(UTC) - timestamp <= STALE_AFTER
