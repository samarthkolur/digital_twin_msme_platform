from datetime import UTC, datetime, timedelta

from copilot.context import context_is_valid


def _state(**overrides: object) -> dict[str, object]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "model_confidence": "high",
        **overrides,
    }


def test_empty_states_is_invalid() -> None:
    assert context_is_valid([]) is False


def test_fresh_high_confidence_state_is_valid() -> None:
    assert context_is_valid([_state()]) is True


def test_stale_state_is_invalid() -> None:
    stale_timestamp = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    assert context_is_valid([_state(timestamp=stale_timestamp)]) is False


def test_low_confidence_state_is_invalid() -> None:
    assert context_is_valid([_state(model_confidence="low")]) is False


def test_malformed_timestamp_is_invalid() -> None:
    assert context_is_valid([_state(timestamp="not-a-timestamp")]) is False


def test_missing_timestamp_is_invalid() -> None:
    state = _state()
    del state["timestamp"]
    assert context_is_valid([state]) is False
