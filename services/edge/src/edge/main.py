import asyncio
import contextlib
import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from paho.mqtt.enums import CallbackAPIVersion

from edge.ml_inference import MLInferenceEngine
from edge.providers import SensorProvider, get_provider
from edge.storage import RawReadingStore, StateStore

logger = logging.getLogger("edge")

SENSOR_PROVIDER = os.environ.get("SENSOR_PROVIDER", "simulated")
ASSET_ID = os.environ.get("ASSET_ID", "motor_01")
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
RAW_MQTT_TOPIC = f"digital-cousin/{ASSET_ID}/raw"
STATE_MQTT_TOPIC = f"digital-cousin/{ASSET_ID}/state"
DATABASE_PATH = os.environ.get("DATABASE_PATH", ":memory:")
PUBLISH_INTERVAL_SECONDS = float(os.environ.get("PUBLISH_INTERVAL_SECONDS", "5"))
# services/ml's ml-trainer job writes here (docker-compose.yml); edge mounts
# the same host path read-only. Absent until a training run has happened
# (design.md §24) — MLInferenceEngine.load() handles that by returning None.
ML_ARTIFACTS_DIR = Path(os.environ.get("ML_ARTIFACTS_DIR", "/app/ml-artifacts"))

_provider: SensorProvider | None = None


async def read_and_publish_once(
    provider: SensorProvider,
    client: mqtt.Client,
    raw_store: RawReadingStore,
    state_store: StateStore,
    ml_engine: MLInferenceEngine | None = None,
) -> None:
    """Reads the active sensor provider once, logs it to SQLite (both the
    Phase 2 raw log and the Phase 3 state history), runs ML inference if a
    trained model is available, and publishes the result to MQTT for
    intra-device consumers.

    A transient read failure (real hardware I/O is flaky) is logged and
    swallowed rather than propagated, so the caller's loop keeps running. An
    ML inference failure is handled the same way — it degrades the reading
    to null anomaly fields rather than dropping the whole cycle.
    """
    try:
        sample = await asyncio.to_thread(provider.read)
    except Exception:
        logger.exception("sensor read failed, skipping this cycle")
        return

    raw_store.insert(ASSET_ID, sample.vibration.rms_g, sample.temperature_c)
    client.publish(
        RAW_MQTT_TOPIC,
        json.dumps(
            {
                "asset_id": ASSET_ID,
                "ts": datetime.now(UTC).isoformat(),
                "vibration_rms_g": sample.vibration.rms_g,
                "temperature_c": sample.temperature_c,
            }
        ),
    )

    ml_result = None
    if ml_engine is not None:
        try:
            ml_result = await asyncio.to_thread(
                ml_engine.infer, sample.raw_vibration_window_g, sample.vibration
            )
        except Exception:
            logger.exception("ML inference failed, leaving anomaly fields null for this reading")

    state_store.insert(ASSET_ID, sample, ml_result)
    state = state_store.latest(ASSET_ID)
    client.publish(STATE_MQTT_TOPIC, json.dumps(state))


async def publish_loop(
    provider: SensorProvider,
    client: mqtt.Client,
    raw_store: RawReadingStore,
    state_store: StateStore,
    ml_engine: MLInferenceEngine | None = None,
) -> None:
    """Calls `read_and_publish_once` on a fixed interval, forever."""
    while True:
        await asyncio.sleep(PUBLISH_INTERVAL_SECONDS)
        await read_and_publish_once(provider, client, raw_store, state_store, ml_engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _provider
    _provider = get_provider(SENSOR_PROVIDER)
    raw_store = RawReadingStore(DATABASE_PATH)
    state_store = StateStore(DATABASE_PATH)
    ml_engine = MLInferenceEngine.load(ML_ARTIFACTS_DIR)

    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    # connect_async + loop_start defer/retry the connection in the background
    # network thread rather than raising if the broker isn't reachable yet
    # (or ever, e.g. in a unit test with no broker running).
    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()

    publish_task = asyncio.create_task(
        publish_loop(_provider, client, raw_store, state_store, ml_engine)
    )

    logger.info(
        "edge service started with provider=%s, ml_inference=%s",
        SENSOR_PROVIDER,
        "enabled" if ml_engine is not None else "disabled",
    )
    try:
        yield
    finally:
        publish_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await publish_task
        client.loop_stop()
        client.disconnect()
        raw_store.close()
        state_store.close()
        _provider.close()
        _provider = None


app = FastAPI(title="Digital Cousin Edge Service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": SENSOR_PROVIDER}
