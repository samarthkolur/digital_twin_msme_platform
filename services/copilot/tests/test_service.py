import asyncio
import json
from datetime import UTC, datetime

import httpx

from copilot.service import LLMClient, QueryEngine


class _FakeLLMClient:
    def __init__(self, response: str = "The motor is healthy.") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response


class _FailingLLMClient:
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("model unavailable")


def _client_with_states(states: list[dict[str, object]]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=json.dumps(states))

    return httpx.AsyncClient(base_url="http://api:8000", transport=httpx.MockTransport(handler))


def _fresh_state(**overrides: object) -> dict[str, object]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "model_confidence": "high",
        "health_index": 0.9,
        "anomaly_score": 0.1,
        "alert_level": "normal",
        "temperature_c": 45.0,
        "vibration": {"rms_g": 0.1, "kurtosis": 3.0},
        **overrides,
    }


def test_answer_calls_the_llm_when_context_is_valid() -> None:
    llm: LLMClient = _FakeLLMClient("Health index is 0.9, all normal.")
    engine = QueryEngine(
        retrieval_client=_client_with_states([_fresh_state()]),
        llm_client=llm,
    )

    response = asyncio.run(engine.answer("Is the motor okay?"))

    assert response.used_fallback is False
    assert response.answer == "Health index is 0.9, all normal."
    assert response.context_size == 1


def test_answer_uses_rule_based_fallback_when_context_is_empty() -> None:
    engine = QueryEngine(
        retrieval_client=_client_with_states([]),
        llm_client=_FakeLLMClient(),
    )

    response = asyncio.run(engine.answer("Is the motor okay?"))

    assert response.used_fallback is True
    assert "don't have any recent sensor data" in response.answer


def test_answer_uses_rule_based_fallback_when_context_is_stale() -> None:
    stale_state = _fresh_state(timestamp="2020-01-01T00:00:00+00:00")
    engine = QueryEngine(
        retrieval_client=_client_with_states([stale_state]),
        llm_client=_FakeLLMClient(),
    )

    response = asyncio.run(engine.answer("Is the motor okay?"))

    assert response.used_fallback is True
    assert "5 minutes" in response.answer


def test_answer_degrades_gracefully_when_the_llm_call_fails() -> None:
    engine = QueryEngine(
        retrieval_client=_client_with_states([_fresh_state()]),
        llm_client=_FailingLLMClient(),
    )

    response = asyncio.run(engine.answer("Is the motor okay?"))

    assert response.used_fallback is True
    assert "dashboard" in response.answer.lower()
