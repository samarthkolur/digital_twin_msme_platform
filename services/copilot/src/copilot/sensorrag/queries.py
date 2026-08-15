"""Held-out SensorRAG query set (design.md §6.4, §9, DD-030).

Spans normal, elevated-anomaly, and no-data/stale/low-confidence state
objects, so the evaluation covers both "answer correctly and grounded" and
"refuse correctly" behavior — design.md §9's two separate metrics
("Factual accuracy" and "Fallback trigger rate: 100%") in one held-out set.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(frozen=True, slots=True)
class SensorRAGCase:
    name: str
    query: str
    states: list[dict[str, Any]]
    expect_fallback: bool


def _state(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "asset_id": "motor_01",
        "timestamp": datetime.now(UTC).isoformat(),
        "vibration": {
            "rms_g": 0.12,
            "kurtosis": 3.1,
            "crest_factor": 4.8,
            "peak_to_peak_g": 2.1,
            "sampling_hz": 3200,
        },
        "temperature_c": 45.0,
        "anomaly_score": 0.1,
        "health_index": 0.92,
        "model_confidence": "high",
        "alert_level": "normal",
    }
    base.update(overrides)
    return base


def default_sensorrag_cases() -> list[SensorRAGCase]:
    normal_state = _state()
    elevated_state = _state(
        health_index=0.55,
        anomaly_score=0.7,
        alert_level="alert",
        vibration={
            "rms_g": 0.9,
            "kurtosis": 8.2,
            "crest_factor": 7.1,
            "peak_to_peak_g": 5.4,
            "sampling_hz": 3200,
        },
    )
    stale_state = _state(timestamp=(datetime.now(UTC) - timedelta(minutes=30)).isoformat())
    low_confidence_state = _state(model_confidence="low")

    return [
        SensorRAGCase(
            name="normal_reading_direct_question",
            query="Is the motor okay right now?",
            states=[normal_state],
            expect_fallback=False,
        ),
        SensorRAGCase(
            name="elevated_anomaly_direct_question",
            query="Is the motor okay right now?",
            states=[elevated_state],
            expect_fallback=False,
        ),
        SensorRAGCase(
            name="alert_explanation",
            query="Why is there an active alert?",
            states=[elevated_state],
            expect_fallback=False,
        ),
        SensorRAGCase(
            name="no_data_available",
            query="Is the motor okay right now?",
            states=[],
            expect_fallback=True,
        ),
        SensorRAGCase(
            name="stale_data",
            query="Is the motor okay right now?",
            states=[stale_state],
            expect_fallback=True,
        ),
        SensorRAGCase(
            name="low_confidence_ood_reading",
            query="Is the motor okay right now?",
            states=[low_confidence_state],
            expect_fallback=True,
        ),
    ]
