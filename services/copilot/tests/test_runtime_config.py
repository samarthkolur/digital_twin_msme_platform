from typing import Any

from copilot.runtime_config import ConfigClient, RuntimeConfig

PAYLOAD = {
    "enablePhase2": True,
    "publishIntervalSeconds": 2.5,
    "alertHealthIndex": 0.5,
    "alertTemperatureC": 65.0,
}
FALLBACK = RuntimeConfig(False, 5.0, 0.6, 70.0)


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_from_env_defaults_to_phase1() -> None:
    assert RuntimeConfig.from_env({}) == FALLBACK


def test_from_env_parses_overrides() -> None:
    config = RuntimeConfig.from_env({"ENABLE_PHASE2": "True", "PUBLISH_INTERVAL_SECONDS": "1"})
    assert config.enable_phase2 is True
    assert config.publish_interval_seconds == 1.0


def test_fetches_and_caches() -> None:
    calls: list[str] = []
    clock = _Clock()

    def fetch(url: str) -> Any:
        calls.append(url)
        return PAYLOAD

    client = ConfigClient(
        "http://config:8002/", FALLBACK, cache_seconds=5, fetch=fetch, clock=clock
    )
    assert client.get() == RuntimeConfig(True, 2.5, 0.5, 65.0)
    clock.now = 4.9
    client.get()
    assert calls == ["http://config:8002/config"]
    clock.now = 5.0
    client.get()
    assert len(calls) == 2


def test_falls_back_then_keeps_last_known_config() -> None:
    clock = _Clock()
    responses: list[Any] = [OSError("down"), PAYLOAD, OSError("down again")]

    def fetch(url: str) -> Any:
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    client = ConfigClient("http://config:8002", FALLBACK, cache_seconds=1, fetch=fetch, clock=clock)
    assert client.get() == FALLBACK
    clock.now = 1
    assert client.get().enable_phase2 is True
    clock.now = 2
    assert client.get().enable_phase2 is True, "an outage keeps the last known config"
