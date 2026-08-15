import asyncio

from copilot.sensorrag.queries import SensorRAGCase, default_sensorrag_cases
from copilot.sensorrag.runner import run_sensorrag_case, run_sensorrag_evaluation
from copilot.service import QueryEngine


class _GroundedLLMClient:
    """Answers without making any numeric claims at all — trivially grounded
    regardless of which case's states it's called with (a fixed numeric
    answer would only be grounded for one specific case's values), standing
    in for a perfectly faithful LLM for the purposes of this test.
    """

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "The machine appears to be operating normally based on the current reading."


class _HallucinatingLLMClient:
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "The health index is 12345.6, which is far outside any plausible range."


def test_default_sensorrag_cases_cover_both_answer_and_fallback_scenarios() -> None:
    cases = default_sensorrag_cases()

    assert any(not c.expect_fallback for c in cases)
    assert any(c.expect_fallback for c in cases)


def test_run_sensorrag_case_marks_correct_fallback_behavior() -> None:
    case = SensorRAGCase(name="no_data", query="Is it okay?", states=[], expect_fallback=True)
    engine = QueryEngine(llm_client=_GroundedLLMClient())

    result = asyncio.run(run_sensorrag_case(engine, case))

    assert result.used_fallback is True
    assert result.fallback_behavior_correct is True
    assert result.grounding is None


def test_run_sensorrag_evaluation_reports_perfect_scores_for_a_faithful_client() -> None:
    engine = QueryEngine(llm_client=_GroundedLLMClient())

    report = asyncio.run(run_sensorrag_evaluation(engine))

    assert report.fallback_accuracy == 1.0
    assert report.hallucination_rate == 0.0


def test_run_sensorrag_evaluation_flags_a_hallucinating_client() -> None:
    engine = QueryEngine(llm_client=_HallucinatingLLMClient())

    report = asyncio.run(run_sensorrag_evaluation(engine))

    assert report.hallucination_rate > 0.0
