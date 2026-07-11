import asyncio
import contextlib
import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from paho.mqtt.enums import CallbackAPIVersion

from edge.providers import SensorProvider, get_provider
from edge.storage import RawReadingStore

logger = logging.getLogger("edge")

SENSOR_PROVIDER = os.environ.get("SENSOR_PROVIDER", "simulated")
ASSET_ID = os.environ.get("ASSET_ID", "motor_01")
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = f"digital-cousin/{ASSET_ID}/raw"
DATABASE_PATH = os.environ.get("DATABASE_PATH", ":memory:")
PUBLISH_INTERVAL_SECONDS = float(os.environ.get("PUBLISH_INTERVAL_SECONDS", "5"))

_provider: SensorProvider | None = None


async def read_and_publish_once(
    provider: SensorProvider,
    client: mqtt.Client,
    store: RawReadingStore,
) -> None:
    """Reads the active sensor provider once, logs the raw reading to SQLite,
    and publishes it to MQTT for intra-device consumers.

    A transient read failure (real hardware I/O is flaky) is logged and
    swallowed rather than propagated, so the caller's loop keeps running.
    """
    try:
        sample = await asyncio.to_thread(provider.read)
    except Exception:
        logger.exception("sensor read failed, skipping this cycle")
        return

    store.insert(ASSET_ID, sample.vibration_rms_g, sample.temperature_c)
    client.publish(
        MQTT_TOPIC,
        json.dumps(
            {
                "asset_id": ASSET_ID,
                "ts": datetime.now(UTC).isoformat(),
                "vibration_rms_g": sample.vibration_rms_g,
                "temperature_c": sample.temperature_c,
            }
        ),
    )


async def publish_loop(
    provider: SensorProvider,
    client: mqtt.Client,
    store: RawReadingStore,
) -> None:
    """Calls `read_and_publish_once` on a fixed interval, forever."""
    while True:
        await asyncio.sleep(PUBLISH_INTERVAL_SECONDS)
        await read_and_publish_once(provider, client, store)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _provider
    _provider = get_provider(SENSOR_PROVIDER)
    store = RawReadingStore(DATABASE_PATH)

    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    # connect_async + loop_start defer/retry the connection in the background
    # network thread rather than raising if the broker isn't reachable yet
    # (or ever, e.g. in a unit test with no broker running).
    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()

    publish_task = asyncio.create_task(publish_loop(_provider, client, store))

    logger.info("edge service started with provider=%s", SENSOR_PROVIDER)
    try:
        yield
    finally:
        publish_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await publish_task
        client.loop_stop()
        client.disconnect()
        store.close()
        _provider.close()
        _provider = None


app = FastAPI(title="Digital Cousin Edge Service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": SENSOR_PROVIDER}
