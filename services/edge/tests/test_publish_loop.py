import asyncio
import json

from edge.main import read_and_publish_once
from edge.providers.simulated import SimulatedSensorProvider
from edge.storage import RawReadingStore


class _FakeMqttClient:
    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []

    def publish(self, topic: str, payload: str) -> None:
        self.published.append((topic, payload))


class _FailingProvider(SimulatedSensorProvider):
    def read(self) -> None:  # type: ignore[override]
        raise RuntimeError("sensor unplugged")


def test_read_and_publish_once_logs_and_publishes() -> None:
    provider = SimulatedSensorProvider()
    client = _FakeMqttClient()
    store = RawReadingStore(":memory:")

    asyncio.run(read_and_publish_once(provider, client, store))  # type: ignore[arg-type]

    assert store.count() == 1
    assert len(client.published) == 1
    topic, payload = client.published[0]
    assert topic == "digital-cousin/motor_01/raw"
    body = json.loads(payload)
    assert body["asset_id"] == "motor_01"
    assert "vibration_rms_g" in body
    assert "temperature_c" in body


def test_read_and_publish_once_swallows_read_failure() -> None:
    provider = _FailingProvider()
    client = _FakeMqttClient()
    store = RawReadingStore(":memory:")

    asyncio.run(read_and_publish_once(provider, client, store))  # type: ignore[arg-type]

    assert store.count() == 0
    assert client.published == []
