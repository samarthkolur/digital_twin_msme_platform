import sqlite3
from typing import Any

# Schema and row mapping are duplicated from `services/edge/src/edge/storage.py`
# (DD-026): edge and api are independent services with no shared Python
# package (see design.md §14), so this table's shape must be kept in sync by
# hand. `IF NOT EXISTS` here lets api start up and answer "no data yet"
# before edge has ever written a row, regardless of container start order.
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


def _row_to_state(row: sqlite3.Row) -> dict[str, Any]:
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


class StateReader:
    """Read-only access to the `state_history` table written by `edge`."""

    def __init__(self, database_path: str) -> None:
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(STATE_HISTORY_SCHEMA)
        self._conn.commit()

    def latest(self, asset_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM state_history WHERE asset_id = ? ORDER BY id DESC LIMIT 1",
            (asset_id,),
        ).fetchone()
        return _row_to_state(row) if row is not None else None

    def history(self, asset_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM state_history WHERE asset_id = ? ORDER BY id DESC LIMIT ?",
            (asset_id, limit),
        ).fetchall()
        return [_row_to_state(row) for row in rows]

    def close(self) -> None:
        self._conn.close()
