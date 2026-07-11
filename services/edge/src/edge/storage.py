import sqlite3
from datetime import UTC, datetime

_SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    vibration_rms_g REAL NOT NULL,
    temperature_c REAL NOT NULL
)
"""


class RawReadingStore:
    """Persists raw sensor readings (design.md §10 Phase 2: "raw data logging").

    This is deliberately separate from the full digital-twin state object
    (design.md §6.0, with anomaly_score/health_index/etc.) — those fields
    depend on the ML pipeline (Phase 4) and state sync (Phase 3), neither of
    which exist yet. This table only records what the sensor actually read.
    """

    def __init__(self, database_path: str) -> None:
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.execute(_SCHEMA)
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
