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

from edge.alerting import AlertThresholds, Buzzer, evaluate_alerts, get_buzzer, highest_level
from edge.ml_inference import MLInferenceEngine
from edge.phase2 import Phase2Inference
from edge.providers import SensorProvider, get_provider
from edge.runtime_config import ConfigClient, RuntimeConfig
from edge.storage import RawReadingStore, StateStore

logger = logging.getLogger("edge")

SENSOR_PROVIDER = os.environ.get("SENSOR_PROVIDER", "simulated")
ASSET_ID = os.environ.get("ASSET_ID", "motor_01")
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
RAW_MQTT_TOPIC = f"digital-cousin/{ASSET_ID}/raw"
STATE_MQTT_TOPIC = f"digital-cousin/{ASSET_ID}/state"
DATABASE_PATH = os.environ.get("DATABASE_PATH", ":memory:")
# The config service holds the runtime settings (enablePhase2, publish
# interval, alert thresholds; design.md DD-047). These environment variables
# are only the fallback used until it first answers.
CONFIG_URL = os.environ.get("CONFIG_URL", "http://localhost:8002")
# services/ml's ml-trainer job writes here (docker-compose.yml); edge mounts
# the same host path read-only. Absent until a training run has happened
# (design.md §24) — MLInferenceEngine.load() handles that by returning None.
ML_ARTIFACTS_DIR = Path(os.environ.get("ML_ARTIFACTS_DIR", "/app/ml-artifacts"))
# Audible alerting. Defaults to "none" so a dev machine or CI container never
# touches GPIO; set BUZZER=gpio on a Pi with a buzzer fitted (design.md §6.2).
BUZZER = os.environ.get("BUZZER", "none")
BUZZER_GPIO_PIN = int(os.environ.get("BUZZER_GPIO_PIN", "18"))

_provider: SensorProvider | None = None


async def read_and_publish_once(
    provider: SensorProvider,
    client: mqtt.Client,
    raw_store: RawReadingStore,
    state_store: StateStore,
    ml_engine: MLInferenceEngine | None = None,
    buzzer: Buzzer | None = None,
    alert_thresholds: AlertThresholds | None = None,
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

    thresholds = alert_thresholds or AlertThresholds()

    ml_result = None
    if ml_engine is not None:
        try:
            ml_result = await asyncio.to_thread(
                ml_engine.infer,
                sample.raw_vibration_window_g,
                sample.vibration,
                thresholds.health_index,
            )
        except Exception:
            logger.exception("ML inference failed, leaving anomaly fields null for this reading")

    state_store.insert(ASSET_ID, sample, ml_result)
    state = state_store.latest(ASSET_ID)
    client.publish(STATE_MQTT_TOPIC, json.dumps(state))

    if buzzer is not None and state is not None:
        alerts = evaluate_alerts(state, thresholds)
        level = highest_level(alerts)
        if level is not None:
            for alert in alerts:
                logger.warning("alert (%s): %s", alert.level, alert.message)
            try:
                # Off-thread: the beep pattern sleeps, and the publish loop's
                # period must not drift because the buzzer is sounding.
                await asyncio.to_thread(buzzer.signal, level)
            except Exception:
                logger.exception("buzzer signal failed, continuing")


async def publish_loop(
    provider: SensorProvider,
    client: mqtt.Client,
    raw_store: RawReadingStore,
    state_store: StateStore,
    config_client: ConfigClient,
    inference: Phase2Inference,
    buzzer: Buzzer | None = None,
) -> None:
    """Calls `read_and_publish_once` on a fixed period, forever.

    The period, the alert thresholds and whether ML inference runs at all
    (enablePhase2) are re-read from the config service every cycle, so a
    change takes effect without restarting the edge.

    The wait is scheduled against a running deadline rather than slept for a
    fixed interval after each cycle, because acquisition is not instantaneous:
    the DS18B20 needs ~750 ms for a 12-bit conversion and the vibration burst
    another 80 ms. Sleeping `PUBLISH_INTERVAL_SECONDS` *after* that work made
    the interval additive, measured at 6.00 s (0.167 Hz) for a configured 5 s.
    If a cycle ever overruns the period the next deadline is pushed forward
    rather than catching up in a burst, so a slow read cannot cause a backlog
    of back-to-back publishes.
    """
    loop = asyncio.get_running_loop()
    config = await asyncio.to_thread(config_client.get)
    next_publish_at = loop.time() + config.publish_interval_seconds
    while True:
        await asyncio.sleep(max(0.0, next_publish_at - loop.time()))
        config = await asyncio.to_thread(config_client.get)
        await read_and_publish_once(
            provider,
            client,
            raw_store,
            state_store,
            inference.engine(config.enable_phase2),
            buzzer,
            AlertThresholds(
                health_index=config.alert_health_index,
                temperature_c=config.alert_temperature_c,
            ),
        )

        interval = config.publish_interval_seconds
        next_publish_at += interval
        if next_publish_at < loop.time():
            next_publish_at = loop.time() + interval


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _provider
    _provider = get_provider(SENSOR_PROVIDER)
    raw_store = RawReadingStore(DATABASE_PATH)
    state_store = StateStore(DATABASE_PATH)
    config_client = ConfigClient(CONFIG_URL, fallback=RuntimeConfig.from_env())
    inference = Phase2Inference(ML_ARTIFACTS_DIR)

    try:
        buzzer = get_buzzer(BUZZER, BUZZER_GPIO_PIN)
    except Exception:
        # A missing or misconfigured buzzer must not stop the twin from
        # monitoring: fall back to the silent path and say so.
        logger.exception("buzzer init failed, continuing without audible alerts")
        buzzer = get_buzzer("none", BUZZER_GPIO_PIN)

    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    # connect_async + loop_start defer/retry the connection in the background
    # network thread rather than raising if the broker isn't reachable yet
    # (or ever, e.g. in a unit test with no broker running).
    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()

    publish_task = asyncio.create_task(
        publish_loop(_provider, client, raw_store, state_store, config_client, inference, buzzer)
    )

    logger.info(
        "edge service started with provider=%s, config=%s, buzzer=%s",
        SENSOR_PROVIDER,
        CONFIG_URL,
        BUZZER,
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
        buzzer.close()
        _provider.close()
        _provider = None


app = FastAPI(title="Digital Cousin Edge Service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": SENSOR_PROVIDER}
