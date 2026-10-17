import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from appconfig.schema import AppConfig, AppConfigUpdate

# One row per setting rather than one JSON blob, so a setting added in a later
# release can be seeded on its own without touching values an operator has
# already changed.
APP_CONFIG_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ConfigStore:
    """Owns the `app_config` table. This service is its only writer."""

    def __init__(self, database_path: str, seed: AppConfig) -> None:
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.execute(APP_CONFIG_SCHEMA)
        now = _now()
        self._conn.executemany(
            "INSERT OR IGNORE INTO app_config (key, value, updated_at) VALUES (?, ?, ?)",
            [(key, json.dumps(value), now) for key, value in seed.model_dump().items()],
        )
        self._conn.commit()

    def get(self) -> AppConfig:
        rows = self._conn.execute("SELECT key, value FROM app_config").fetchall()
        known = AppConfig.model_fields
        # Ignore rows for settings a newer release added and this one doesn't
        # know, so a downgrade does not fail on startup.
        values: dict[str, Any] = {key: json.loads(value) for key, value in rows if key in known}
        return AppConfig.model_validate(values)

    def update(self, update: AppConfigUpdate) -> AppConfig:
        changes = update.model_dump(exclude_none=True)
        # Validate the merged result before writing anything.
        merged = self.get().model_copy(update=changes)
        AppConfig.model_validate(merged.model_dump())
        now = _now()
        self._conn.executemany(
            "UPDATE app_config SET value = ?, updated_at = ? WHERE key = ?",
            [(json.dumps(value), now, key) for key, value in changes.items()],
        )
        self._conn.commit()
        return self.get()

    def close(self) -> None:
        self._conn.close()
