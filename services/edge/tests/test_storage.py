from edge.providers.base import SensorSample, VibrationFeatures
from edge.storage import RawReadingStore, StateStore


def test_insert_and_count() -> None:
    store = RawReadingStore(":memory:")
    try:
        assert store.count() == 0

        store.insert("motor_01", vibration_rms_g=0.12, temperature_c=45.5)
        store.insert("motor_01", vibration_rms_g=0.34, temperature_c=46.1)

        assert store.count() == 2
    finally:
        store.close()


def test_insert_persists_expected_columns() -> None:
    store = RawReadingStore(":memory:")
    try:
        store.insert("motor_01", vibration_rms_g=0.12, temperature_c=45.5)

        row = store._conn.execute(
            "SELECT asset_id, vibration_rms_g, temperature_c FROM raw_readings"
        ).fetchone()

        assert row == ("motor_01", 0.12, 45.5)
    finally:
        store.close()


def _sample() -> SensorSample:
    return SensorSample(
        vibration=VibrationFeatures(
            rms_g=0.12,
            kurtosis=3.1,
            crest_factor=4.8,
            peak_to_peak_g=2.1,
            sampling_hz=3200,
        ),
        temperature_c=54.3,
        raw_vibration_window_g=[1.0, 1.1, 0.9, 1.05],
    )


def test_state_store_latest_returns_none_when_empty() -> None:
    store = StateStore(":memory:")
    try:
        assert store.latest("motor_01") is None
    finally:
        store.close()


def test_state_store_insert_and_latest() -> None:
    store = StateStore(":memory:")
    try:
        store.insert("motor_01", _sample())

        state = store.latest("motor_01")

        assert state is not None
        assert state["asset_id"] == "motor_01"
        assert state["vibration"] == {
            "rms_g": 0.12,
            "kurtosis": 3.1,
            "crest_factor": 4.8,
            "peak_to_peak_g": 2.1,
            "sampling_hz": 3200,
        }
        assert state["temperature_c"] == 54.3
        # ML-derived fields are unpopulated until Phase 4 (DD-023).
        assert state["anomaly_score"] is None
        assert state["health_index"] is None
        assert state["model_confidence"] is None
        assert state["alert_level"] is None
    finally:
        store.close()


def test_state_store_history_returns_most_recent_first() -> None:
    store = StateStore(":memory:")
    try:
        store.insert("motor_01", _sample())
        store.insert(
            "motor_01",
            SensorSample(
                vibration=VibrationFeatures(
                    rms_g=0.99, kurtosis=3.0, crest_factor=4.0, peak_to_peak_g=2.0, sampling_hz=3200
                ),
                temperature_c=60.0,
                raw_vibration_window_g=[1.0, 1.1, 0.9, 1.05],
            ),
        )

        history = store.history("motor_01", limit=10)

        assert len(history) == 2
        assert history[0]["vibration"]["rms_g"] == 0.99  # most recent first
        assert history[1]["vibration"]["rms_g"] == 0.12
    finally:
        store.close()


def test_state_store_scopes_by_asset_id() -> None:
    store = StateStore(":memory:")
    try:
        store.insert("motor_01", _sample())

        assert store.latest("other_machine") is None
        assert store.history("other_machine") == []
    finally:
        store.close()
