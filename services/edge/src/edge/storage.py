import sqlite3
from datetime import UTC, datetime
from typing import Any

from edge.ml_inference import MLInferenceResult
from edge.providers.base import SensorSample

_RAW_READINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    vibration_rms_g REAL NOT NULL,
    temperature_c REAL NOT NULL
)
"""

# Column names/order are duplicated in `services/api/src/api/storage.py`
# (DD-026) since edge and api are independent services with no shared
# Python package (per §14) — keep the two schemas in sync by hand.
STATE_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    vibration_rms_g REAL NOT NULL,
    vibration_kurtosis REAL NOT NULL,
    vibration_crest_factor REAL NOT NULL,
    vibration_peak_to_peak_g REAL NOT NULL,
    vibration_sampling_hz INTEGER NOT NULL,
    temperature_c REAL NOT NULL,
    anomaly_score REAL,
    health_index REAL,
    model_confidence TEXT,
    alert_level TEXT
)
"""


def state_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Maps a `state_history` row to the §6.0 state-object JSON shape.

    Shared by `edge` (which writes this table) and duplicated in
    `services/api` (which only reads it) since there's no shared package to
    import it from (see the schema comment above).
    """
    return {
        "asset_id": row["asset_id"],
        "timestamp": row["ts"],
        "vibration": {
            "rms_g": row["vibration_rms_g"],
            "kurtosis": row["vibration_kurtosis"],
            "crest_factor": row["vibration_crest_factor"],
            "peak_to_peak_g": row["vibration_peak_to_peak_g"],
            "sampling_hz": row["vibration_sampling_hz"],
        },
        "temperature_c": row["temperature_c"],
        "anomaly_score": row["anomaly_score"],
        "health_index": row["health_index"],
        "model_confidence": row["model_confidence"],
        "alert_level": row["alert_level"],
    }


class RawReadingStore:
    """Persists raw sensor readings (design.md §10 Phase 2: "raw data logging").

    This is deliberately separate from the full digital-twin state object
    (design.md §6.0, with anomaly_score/health_index/etc.) — those fields
    depend on the ML pipeline (Phase 4) and state sync (Phase 3), neither of
    which exist yet. This table only records what the sensor actually read.
    """

    def __init__(self, database_path: str) -> None:
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.execute(_RAW_READINGS_SCHEMA)
        self._conn.commit()

    def insert(self, asset_id: str, vibration_rms_g: float, temperature_c: float) -> None:
        self._conn.execute(
            "INSERT INTO raw_readings (asset_id, ts, vibration_rms_g, temperature_c) "
            "VALUES (?, ?, ?, ?)",
            (asset_id, datetime.now(UTC).isoformat(), vibration_rms_g, temperature_c),
        )
        self._conn.commit()

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM raw_readings").fetchone()
        return int(row[0])

    def close(self) -> None:
        self._conn.close()


class StateStore:
    """Persists the full digital-twin state object (design.md §6.0) to the
    `state_history` table — distinct from `RawReadingStore` (DD-023):
    `anomaly_score`/`health_index`/`model_confidence`/`alert_level` are left
    NULL until the ML pipeline (Phase 4) exists to populate them.
    """

    def __init__(self, database_path: str) -> None:
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(STATE_HISTORY_SCHEMA)
        self._conn.commit()

    def insert(
        self, asset_id: str, sample: SensorSample, ml_result: MLInferenceResult | None = None
    ) -> None:
        """`ml_result` is `None` whenever no ML artifacts have been trained
        yet (design.md §24) — anomaly_score/health_index/model_confidence/
        alert_level are left NULL in that case, exactly as before
        `edge.ml_inference` existed (DD-023).
        """
        self._conn.execute(
            "INSERT INTO state_history ("
            "  asset_id, ts, vibration_rms_g, vibration_kurtosis,"
            "  vibration_crest_factor, vibration_peak_to_peak_g,"
            "  vibration_sampling_hz, temperature_c,"
            "  anomaly_score, health_index, model_confidence, alert_level"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                asset_id,
                datetime.now(UTC).isoformat(),
                sample.vibration.rms_g,
                sample.vibration.kurtosis,
                sample.vibration.crest_factor,
                sample.vibration.peak_to_peak_g,
                sample.vibration.sampling_hz,
                sample.temperature_c,
                ml_result.anomaly_score if ml_result is not None else None,
                ml_result.health_index if ml_result is not None else None,
                ml_result.model_confidence if ml_result is not None else None,
                ml_result.alert_level if ml_result is not None else None,
            ),
        )
        self._conn.commit()

    def latest(self, asset_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM state_history WHERE asset_id = ? ORDER BY id DESC LIMIT 1",
            (asset_id,),
        ).fetchone()
        return state_row_to_dict(row) if row is not None else None

    def history(self, asset_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM state_history WHERE asset_id = ? ORDER BY id DESC LIMIT ?",
            (asset_id, limit),
        ).fetchall()
        return [state_row_to_dict(row) for row in rows]

    def close(self) -> None:
        self._conn.close()
