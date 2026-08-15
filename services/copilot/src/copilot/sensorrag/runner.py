"""SensorRAG evaluation runner (design.md §6.4, §9, DD-030).

Runs the held-out query set (`copilot.sensorrag.queries`) against a
`QueryEngine`, using `answer_with_context` so each case's state objects are
injected directly rather than requiring a live `api` service — this makes
the evaluation deterministic and runnable in CI/tests, not just against a
live deployed stack.
"""

import asyncio
import logging
from dataclasses import dataclass

from copilot.sensorrag.grounding import GroundingResult, check_numeric_grounding
from copilot.sensorrag.queries import SensorRAGCase, default_sensorrag_cases
from copilot.service import QueryEngine

logger = logging.getLogger("copilot.sensorrag")


@dataclass(frozen=True, slots=True)
class SensorRAGCaseResult:
    case_name: str
    answer: str
    used_fallback: bool
    expected_fallback: bool
    fallback_behavior_correct: bool
    # None when used_fallback=True — a fallback response has no LLM-generated
    # numeric claims to check for grounding.
    grounding: GroundingResult | None


@dataclass(frozen=True, slots=True)
class SensorRAGReport:
    results: list[SensorRAGCaseResult]

    @property
    def fallback_accuracy(self) -> float:
        """Matches design.md §9's "Fallback trigger rate" metric (target
        100%) — the fraction of cases where the copilot correctly chose to
        answer vs. correctly chose to refuse.
        """
        if not self.results:
            return 1.0
        correct = sum(1 for r in self.results if r.fallback_behavior_correct)
        return correct / len(self.results)

    @property
    def hallucination_rate(self) -> float:
        """Fraction of *LLM-answered* (non-fallback) cases with at least one
        ungrounded numeric claim. design.md §9's target for the underlying
        metric: 0 untraceable numeric claims across the held-out set.
        """
        answered = [r for r in self.results if r.grounding is not None]
        if not answered:
            return 0.0
        hallucinated = sum(
            1 for r in answered if r.grounding is not None and not r.grounding.is_fully_grounded
        )
        return hallucinated / len(answered)


async def run_sensorrag_case(engine: QueryEngine, case: SensorRAGCase) -> SensorRAGCaseResult:
    response = await engine.answer_with_context(case.query, case.states)
    grounding = (
        None if response.used_fallback else check_numeric_grounding(response.answer, case.states)
    )
    return SensorRAGCaseResult(
        case_name=case.name,
        answer=response.answer,
        used_fallback=response.used_fallback,
        expected_fallback=case.expect_fallback,
        fallback_behavior_correct=response.used_fallback == case.expect_fallback,
        grounding=grounding,
    )


async def run_sensorrag_evaluation(
    engine: QueryEngine, cases: list[SensorRAGCase] | None = None
) -> SensorRAGReport:
    resolved_cases = cases if cases is not None else default_sensorrag_cases()
    results = [await run_sensorrag_case(engine, case) for case in resolved_cases]
    return SensorRAGReport(results=results)


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    engine = QueryEngine()
    report = await run_sensorrag_evaluation(engine)

    for result in report.results:
        status = "OK" if result.fallback_behavior_correct else "WRONG"
        logger.info(
            "[%s] fallback=%s (expected %s) [%s]",
            result.case_name,
            result.used_fallback,
            result.expected_fallback,
            status,
        )
        if result.grounding is not None:
            logger.info(
                "  numeric claims: %d, ungrounded: %s",
                result.grounding.total_numeric_claims,
                result.grounding.ungrounded_claims,
            )

    logger.info("Fallback accuracy: %.2f%%", report.fallback_accuracy * 100)
    logger.info("Hallucination rate: %.2f%%", report.hallucination_rate * 100)


if __name__ == "__main__":
    asyncio.run(_main())
