from copilot.sensorrag.grounding import (
    check_numeric_grounding,
    extract_numeric_claims,
    is_claim_grounded,
)


def _state(**overrides: object) -> dict[str, object]:
    return {
        "health_index": 0.71,
        "anomaly_score": 0.3,
        "temperature_c": 61.0,
        "vibration": {"rms_g": 0.42, "kurtosis": 4.8, "crest_factor": 5.0, "peak_to_peak_g": 2.1},
        **overrides,
    }


def test_extract_numeric_claims_finds_all_numbers() -> None:
    claims = extract_numeric_claims("Health index is 0.71 and temperature is 61 degrees.")
    assert claims == [0.71, 61.0]


def test_is_claim_grounded_within_tolerance() -> None:
    assert is_claim_grounded(0.71, [0.71]) is True
    assert is_claim_grounded(0.715, [0.71]) is True  # within 2% relative tolerance
    assert is_claim_grounded(5.0, [0.71]) is False


def test_check_numeric_grounding_all_grounded() -> None:
    answer = "The motor's health index is 0.71, and the temperature is 61 degrees."
    result = check_numeric_grounding(answer, [_state()])

    assert result.total_numeric_claims == 2
    assert result.is_fully_grounded is True
    assert result.ungrounded_claims == []


def test_check_numeric_grounding_detects_a_hallucinated_number() -> None:
    answer = "The motor's health index is 0.71, but vibration RMS spiked to 99.9 g."
    result = check_numeric_grounding(answer, [_state()])

    assert result.is_fully_grounded is False
    assert 99.9 in result.ungrounded_claims


def test_check_numeric_grounding_with_no_numeric_claims_is_trivially_grounded() -> None:
    result = check_numeric_grounding("The motor appears to be running normally.", [_state()])

    assert result.total_numeric_claims == 0
    assert result.is_fully_grounded is True
