from pathlib import Path

import pytest
from pydantic import ValidationError

from appconfig.schema import AppConfig, AppConfigUpdate, seed_config_from_env
from appconfig.store import ConfigStore


def test_seed_defaults_to_phase1_only() -> None:
    config = seed_config_from_env({})
    assert config.enable_phase2 is False
    assert config.publish_interval_seconds == 5.0
    assert config.alert_health_index == 0.6
    assert config.alert_temperature_c == 70.0


def test_seed_takes_overrides_from_env() -> None:
    config = seed_config_from_env({"ENABLE_PHASE2": "true", "ALERT_TEMPERATURE_C": "65"})
    assert config.enable_phase2 is True
    assert config.alert_temperature_c == 65.0


def test_seed_rejects_out_of_range_env() -> None:
    with pytest.raises(ValidationError):
        seed_config_from_env({"ALERT_HEALTH_INDEX": "1.5"})


def test_store_round_trips_and_persists(tmp_path: Path) -> None:
    db = str(tmp_path / "config.sqlite3")
    store = ConfigStore(db, AppConfig())
    updated = store.update(AppConfigUpdate(enable_phase2=True, alert_temperature_c=80))
    assert updated.enable_phase2 is True
    assert updated.alert_temperature_c == 80
    store.close()

    reopened = ConfigStore(db, AppConfig())
    assert reopened.get() == updated
    reopened.close()


def test_reseeding_never_overwrites_operator_changes(tmp_path: Path) -> None:
    db = str(tmp_path / "config.sqlite3")
    store = ConfigStore(db, AppConfig())
    store.update(AppConfigUpdate(enable_phase2=True))
    store.close()

    # A restart seeds again (e.g. with ENABLE_PHASE2 unset); the stored value wins.
    restarted = ConfigStore(db, AppConfig(enable_phase2=False))
    assert restarted.get().enable_phase2 is True
    restarted.close()


def test_store_ignores_unknown_keys(tmp_path: Path) -> None:
    db = str(tmp_path / "config.sqlite3")
    store = ConfigStore(db, AppConfig())
    store._conn.execute(
        "INSERT INTO app_config (key, value, updated_at) VALUES ('fromNewerRelease', '1', 'x')"
    )
    store._conn.commit()
    assert store.get() == AppConfig()
    store.close()


def test_update_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        AppConfigUpdate.model_validate({"publishIntervalSeconds": 0})
    with pytest.raises(ValidationError):
        AppConfigUpdate.model_validate({"unknownSetting": True})
