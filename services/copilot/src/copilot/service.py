"""Query orchestration (design.md §6.4): retrieve -> validate context ->
rule-based fallback OR LLM call, dispatched by COPILOT_LLM_MODE.
"""

import os
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from copilot.context import context_is_valid
from copilot.fallback import llm_unavailable_response, rule_based_response
from copilot.prompt import SYSTEM_PROMPT, build_user_prompt
from copilot.retrieval import retrieve_recent_states


class LLMClient(Protocol):
    async def generate(self, system_prompt: str, user_prompt: str) -> str: ...


@dataclass(frozen=True, slots=True)
class QueryResponse:
    answer: str
    used_fallback: bool
    context_size: int


def _build_llm_client(mode: str) -> LLMClient:
    if mode == "local":
        from copilot.llm_local import LocalLlamaClient

        return LocalLlamaClient()
    if mode == "api":
        from copilot.llm_api import ApiLlmClient

        return ApiLlmClient()
    raise ValueError(f"Unknown COPILOT_LLM_MODE: {mode!r}")


class QueryEngine:
    """Instantiated once at app startup. The LLM client itself is built
    lazily on first use of the LLM path (not at startup) so a missing local
    model file or API key doesn't crash service startup — the rule-based
    fallback path always works regardless (design.md §6.4).
    """

    def __init__(
        self,
        llm_mode: str | None = None,
        retrieval_client: httpx.AsyncClient | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self._llm_mode = llm_mode or os.environ.get("COPILOT_LLM_MODE", "local")
        self._retrieval_client = retrieval_client
        self._llm_client: LLMClient | None = llm_client

    async def answer(self, query: str) -> QueryResponse:
        states = await retrieve_recent_states(client=self._retrieval_client)
        return await self.answer_with_context(query, states)

    async def answer_with_context(self, query: str, states: list[dict[str, Any]]) -> QueryResponse:
        """Same logic as `answer`, but with the retrieved state objects
        supplied directly rather than fetched from `api` — used by the
        SensorRAG evaluation harness (`copilot.sensorrag`, design.md DD-030)
        to run deterministic held-out cases without a live api service.
        """
        if not context_is_valid(states):
            return QueryResponse(
                answer=rule_based_response(states), used_fallback=True, context_size=len(states)
            )

        try:
            if self._llm_client is None:
                self._llm_client = _build_llm_client(self._llm_mode)
            answer = await self._llm_client.generate(
                SYSTEM_PROMPT, build_user_prompt(query, states)
            )
            return QueryResponse(answer=answer, used_fallback=False, context_size=len(states))
        except Exception:
            # Any LLM-path failure (missing weights, missing API key, network
            # error, ...) degrades to a fallback response rather than a 500 —
            # design.md §6.4's "never answer ungrounded" intent extends to
            # never answering with a broken LLM call either.
            return QueryResponse(
                answer=llm_unavailable_response(), used_fallback=True, context_size=len(states)
            )
