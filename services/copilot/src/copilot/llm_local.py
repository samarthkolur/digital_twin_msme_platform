"""Local TinyLlama-1.1B Q4_K_M inference via llama.cpp (design.md §6.4, §7).

`llama-cpp-python` is an optional extra (`local-llm`, services/copilot's
pyproject.toml) since it compiles native code at install time — the import
is deferred to `__init__` so the rest of the copilot service (retrieval,
context validation, rule-based fallback, the API-mode client) works without
that extra installed, and so a missing extra fails with a clear message only
when `COPILOT_LLM_MODE=local` is actually used.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

MODEL_PATH = Path(os.environ.get("LOCAL_LLM_MODEL_PATH", "/app/models/tinyllama-1.1b-q4_k_m.gguf"))


class LocalLlamaClient:
    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "COPILOT_LLM_MODE=local needs the `local-llm` extra "
                "(`uv sync --extra local-llm`, design.md §16) — llama-cpp-python isn't "
                "installed by default since it compiles native code."
            ) from exc

        if not model_path.exists():
            raise FileNotFoundError(
                f"No local LLM weights at {model_path} — download TinyLlama-1.1B Q4_K_M "
                f"(design.md §7) or set COPILOT_LLM_MODE=api instead."
            )
        self._llama: Any = Llama(model_path=str(model_path), n_ctx=2048)

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        def _run() -> str:
            response = self._llama.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            return str(response["choices"][0]["message"]["content"])

        return await asyncio.to_thread(_run)
