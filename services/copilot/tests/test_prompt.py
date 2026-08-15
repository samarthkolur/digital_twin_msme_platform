from copilot.prompt import SYSTEM_PROMPT, build_user_prompt, format_context


def _state(**overrides: object) -> dict[str, object]:
    return {
        "timestamp": "2026-07-01T09:32:15Z",
        "health_index": 0.71,
        "anomaly_score": 0.3,
        "alert_level": "normal",
        "temperature_c": 54.3,
        "vibration": {"rms_g": 0.42, "kurtosis": 4.8},
        **overrides,
    }


def test_system_prompt_forbids_ungrounded_answers() -> None:
    assert "ONLY" in SYSTEM_PROMPT
    assert "grounded" in SYSTEM_PROMPT.lower()


def test_format_context_includes_key_fields() -> None:
    text = format_context([_state()])

    assert "health_index=0.71" in text
    assert "vibration_rms_g=0.42" in text
    assert "kurtosis=4.8" in text
    assert "temperature_c=54.3" in text


def test_format_context_handles_missing_vibration_gracefully() -> None:
    state = _state()
    del state["vibration"]

    text = format_context([state])

    assert "vibration_rms_g=None" in text


def test_build_user_prompt_includes_the_query_and_context() -> None:
    prompt = build_user_prompt("Is the motor okay?", [_state()])

    assert "Is the motor okay?" in prompt
    assert "health_index=0.71" in prompt
