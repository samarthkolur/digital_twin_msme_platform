import asyncio
import json

from edge.main import read_and_publish_once
from edge.providers.simulated import SimulatedSensorProvider
from edge.storage import RawReadingStore, StateStore


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
    raw_store = RawReadingStore(":memory:")
    state_store = StateStore(":memory:")

    asyncio.run(
        read_and_publish_once(provider, client, raw_store, state_store)  # type: ignore[arg-type]
    )

    assert raw_store.count() == 1
    assert state_store.latest("motor_01") is not None
    assert len(client.published) == 2

    raw_topic, raw_payload = client.published[0]
    assert raw_topic == "digital-cousin/motor_01/raw"
    raw_body = json.loads(raw_payload)
    assert raw_body["asset_id"] == "motor_01"
    assert "vibration_rms_g" in raw_body
    assert "temperature_c" in raw_body

    state_topic, state_payload = client.published[1]
    assert state_topic == "digital-cousin/motor_01/state"
    state_body = json.loads(state_payload)
    assert state_body["asset_id"] == "motor_01"
    assert "rms_g" in state_body["vibration"]
    assert "kurtosis" in state_body["vibration"]
    assert state_body["anomaly_score"] is None
    assert state_body["health_index"] is None


def test_read_and_publish_once_swallows_read_failure() -> None:
    provider = _FailingProvider()
    client = _FakeMqttClient()
    raw_store = RawReadingStore(":memory:")
    state_store = StateStore(":memory:")

    asyncio.run(
        read_and_publish_once(provider, client, raw_store, state_store)  # type: ignore[arg-type]
    )

    assert raw_store.count() == 0
    assert state_store.latest("motor_01") is None
    assert client.published == []
