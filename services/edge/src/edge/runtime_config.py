"""Runtime configuration from the config service (design.md DD-047).

The edge keeps monitoring when the config service is unreachable: it uses the
last config it fetched, or, before the first successful fetch, the values from
its own environment (the same defaults the config service seeds from). The
client is deliberately stdlib-only so the edge gains no HTTP dependency.

Kept in sync by hand with services/config's AppConfig and with the copilot's
copy of this client: services share no Python package (DD-002).
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("edge.runtime_config")

# Long enough that a 5 s publish cycle reuses one fetch, short enough that a
# change made on the dashboard takes effect within one or two cycles.
DEFAULT_CACHE_SECONDS = 5.0
REQUEST_TIMEOUT_SECONDS = 2.0


@dataclass(frozen=True)
class RuntimeConfig:
    enable_phase2: bool
    publish_interval_seconds: float
    alert_health_index: float
    alert_temperature_c: float
    alert_critical_fraction: float = 0.75
    copilot_llm_mode: str = "local"
    copilot_stale_after_seconds: int = 300
    copilot_context_size: int = 10

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> RuntimeConfig:
        env = os.environ if environ is None else environ
        return cls(
            enable_phase2=env.get("ENABLE_PHASE2", "false").strip().lower() in ("1", "true", "yes"),
            publish_interval_seconds=float(env.get("PUBLISH_INTERVAL_SECONDS", "5")),
            alert_health_index=float(env.get("ALERT_HEALTH_INDEX", "0.6")),
            alert_temperature_c=float(env.get("ALERT_TEMPERATURE_C", "70")),
            copilot_llm_mode=env.get("COPILOT_LLM_MODE", "local"),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> RuntimeConfig:
        return cls(
            enable_phase2=bool(payload["enablePhase2"]),
            publish_interval_seconds=float(payload["publishIntervalSeconds"]),
            alert_health_index=float(payload["alertHealthIndex"]),
            alert_temperature_c=float(payload["alertTemperatureC"]),
            # .get(): tolerate a config service from before these settings
            # existed, so the two can be upgraded in either order.
            alert_critical_fraction=float(payload.get("alertCriticalFraction", 0.75)),
            copilot_llm_mode=str(payload.get("copilotLlmMode", "local")),
            copilot_stale_after_seconds=int(payload.get("copilotStaleAfterSeconds", 300)),
            copilot_context_size=int(payload.get("copilotContextSize", 10)),
        )


def _http_get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.load(response)


class ConfigClient:
    def __init__(
        self,
        base_url: str,
        fallback: RuntimeConfig,
        cache_seconds: float = DEFAULT_CACHE_SECONDS,
        fetch: Callable[[str], Any] = _http_get_json,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = base_url.rstrip("/") + "/config"
        self._current = fallback
        self._cache_seconds = cache_seconds
        self._fetch = fetch
        self._clock = clock
        self._fetched_at: float | None = None
        self._failing = False

    def get(self) -> RuntimeConfig:
        now = self._clock()
        if self._fetched_at is not None and now - self._fetched_at < self._cache_seconds:
            return self._current
        try:
            self._current = RuntimeConfig.from_payload(self._fetch(self._url))
            if self._failing:
                logger.info("config service reachable again")
            self._failing = False
        except Exception:
            # Log once per outage, not once per cycle.
            if not self._failing:
                logger.warning(
                    "config service unreachable at %s, using last known config",
                    self._url,
                    exc_info=True,
                )
            self._failing = True
        self._fetched_at = now
        return self._current
