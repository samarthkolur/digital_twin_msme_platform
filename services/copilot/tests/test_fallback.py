from copilot.fallback import llm_unavailable_response, rule_based_response


def test_empty_context_message_mentions_no_data() -> None:
    message = rule_based_response([])
    assert "don't have any recent sensor data" in message


def test_low_confidence_message_mentions_confidence() -> None:
    message = rule_based_response([{"model_confidence": "low"}])
    assert "low-confidence" in message


def test_stale_message_mentions_5_minutes() -> None:
    message = rule_based_response([{"model_confidence": "high"}])
    assert "5 minutes" in message


def test_llm_unavailable_message_points_to_the_dashboard() -> None:
    assert "dashboard" in llm_unavailable_response().lower()
