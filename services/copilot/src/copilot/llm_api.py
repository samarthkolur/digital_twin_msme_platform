"""API-based LLM fallback (design.md §6.4, §7) — used when
COPILOT_LLM_MODE=api. Reads provider credentials from the environment (only
ever populated from the external $SECRETS_FILE, DD-010 — never committed to
this repo).
"""

import os

import httpx

_TIMEOUT_SECONDS = 15.0  # design.md §6.4: "<2 s API fallback" typical; generous ceiling here


class ApiLlmClient:
    def __init__(self, provider: str | None = None) -> None:
        self._provider = provider or os.environ.get("COPILOT_API_PROVIDER", "anthropic")

        if self._provider == "anthropic":
            self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            self._model = os.environ.get("COPILOT_API_MODEL", "claude-sonnet-5")
        elif self._provider == "openai":
            self._api_key = os.environ.get("OPENAI_API_KEY", "")
            self._model = os.environ.get("COPILOT_API_MODEL", "gpt-4o-mini")
        else:
            raise ValueError(f"Unknown COPILOT_API_PROVIDER: {self._provider!r}")

        if not self._api_key:
            raise RuntimeError(
                f"COPILOT_LLM_MODE=api needs {self._provider.upper()}_API_KEY set in "
                f"$SECRETS_FILE (design.md DD-010)."
            )

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            if self._provider == "anthropic":
                return await self._generate_anthropic(client, system_prompt, user_prompt)
            return await self._generate_openai(client, system_prompt, user_prompt)

    async def _generate_anthropic(
        self, client: httpx.AsyncClient, system_prompt: str, user_prompt: str
    ) -> str:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": 512,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        )
        response.raise_for_status()
        body = response.json()
        return str(body["content"][0]["text"])

    async def _generate_openai(
        self, client: httpx.AsyncClient, system_prompt: str, user_prompt: str
    ) -> str:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        response.raise_for_status()
        body = response.json()
        return str(body["choices"][0]["message"]["content"])
