"""Query orchestration (design.md §6.4): retrieve -> validate context ->
rule-based fallback OR LLM call, dispatched by the configured LLM mode.

The LLM mode, context size and freshness window come from the project config
(design.md DD-047) per query, so changing them takes effect on the next
question without restarting the copilot.
"""

import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Protocol

import httpx

from copilot.context import STALE_AFTER, context_is_valid
from copilot.fallback import llm_unavailable_response, rule_based_response
from copilot.prompt import SYSTEM_PROMPT, build_user_prompt
from copilot.retrieval import DEFAULT_RETRIEVAL_LIMIT, retrieve_recent_states
from copilot.runtime_config import RuntimeConfig


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
        self._default_llm_mode = llm_mode or os.environ.get("COPILOT_LLM_MODE", "local")
        self._retrieval_client = retrieval_client
        # An injected client (tests, the SensorRAG harness) serves every mode.
        self._injected_llm_client = llm_client
        # Built lazily and kept per mode, so switching copilotLlmMode back and
        # forth doesn't reload a local model each time.
        self._llm_clients: dict[str, LLMClient] = {}

    async def answer(self, query: str, config: RuntimeConfig | None = None) -> QueryResponse:
        limit = config.copilot_context_size if config else DEFAULT_RETRIEVAL_LIMIT
        states = await retrieve_recent_states(limit=limit, client=self._retrieval_client)
        return await self.answer_with_context(
            query,
            states,
            stale_after=(
                timedelta(seconds=config.copilot_stale_after_seconds) if config else STALE_AFTER
            ),
            llm_mode=config.copilot_llm_mode if config else None,
        )

    async def answer_with_context(
        self,
        query: str,
        states: list[dict[str, Any]],
        stale_after: timedelta = STALE_AFTER,
        llm_mode: str | None = None,
    ) -> QueryResponse:
        """Same logic as `answer`, but with the retrieved state objects
        supplied directly rather than fetched from `api` — used by the
        SensorRAG evaluation harness (`copilot.sensorrag`, design.md DD-030)
        to run deterministic held-out cases without a live api service.
        """
        if not context_is_valid(states, stale_after):
            return QueryResponse(
                answer=rule_based_response(states, stale_after),
                used_fallback=True,
                context_size=len(states),
            )

        try:
            llm_client = self._llm_client_for(llm_mode or self._default_llm_mode)
            answer = await llm_client.generate(SYSTEM_PROMPT, build_user_prompt(query, states))
            return QueryResponse(answer=answer, used_fallback=False, context_size=len(states))
        except Exception:
            # Any LLM-path failure (missing weights, missing API key, network
            # error, ...) degrades to a fallback response rather than a 500 —
            # design.md §6.4's "never answer ungrounded" intent extends to
            # never answering with a broken LLM call either.
            return QueryResponse(
                answer=llm_unavailable_response(), used_fallback=True, context_size=len(states)
            )

    def _llm_client_for(self, mode: str) -> LLMClient:
        if self._injected_llm_client is not None:
            return self._injected_llm_client
        if mode not in self._llm_clients:
            self._llm_clients[mode] = _build_llm_client(mode)
        return self._llm_clients[mode]
