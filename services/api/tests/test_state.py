import importlib
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.main
from api.storage import STATE_HISTORY_SCHEMA


def _seed(db_path: Path, *, rms_g: float, asset_id: str = "motor_01") -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(STATE_HISTORY_SCHEMA)
        conn.execute(
            "INSERT INTO state_history ("
            "  asset_id, ts, vibration_rms_g, vibration_kurtosis,"
            "  vibration_crest_factor, vibration_peak_to_peak_g,"
            "  vibration_sampling_hz, temperature_c"
            ") VALUES (?, '2026-07-01T09:32:15+00:00', ?, 3.1, 4.8, 2.1, 3200, 54.3)",
            (asset_id, rms_g),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def app_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, Path]]:
    db_path = tmp_path / "state.sqlite3"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    importlib.reload(api.main)
    with TestClient(api.main.app) as client:
        yield client, db_path


def test_state_current_404_when_no_data(app_client: tuple[TestClient, Path]) -> None:
    client, _ = app_client

    response = client.get("/state/current")

    assert response.status_code == 404


def test_state_current_returns_latest_reading(app_client: tuple[TestClient, Path]) -> None:
    client, db_path = app_client
    _seed(db_path, rms_g=0.42)

    response = client.get("/state/current")

    assert response.status_code == 200
    body = response.json()
    assert body["asset_id"] == "motor_01"
    assert body["vibration"] == {
        "rms_g": 0.42,
        "kurtosis": 3.1,
        "crest_factor": 4.8,
        "peak_to_peak_g": 2.1,
        "sampling_hz": 3200,
    }
    assert body["temperature_c"] == 54.3
    assert body["anomaly_score"] is None
    assert body["health_index"] is None


def test_state_history_returns_most_recent_first(app_client: tuple[TestClient, Path]) -> None:
    client, db_path = app_client
    _seed(db_path, rms_g=0.10)
    _seed(db_path, rms_g=0.20)

    response = client.get("/state/history", params={"limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["vibration"]["rms_g"] == 0.20
    assert body[1]["vibration"]["rms_g"] == 0.10


def test_state_current_scopes_by_asset_id(app_client: tuple[TestClient, Path]) -> None:
    client, db_path = app_client
    _seed(db_path, rms_g=0.42, asset_id="other_machine")

    response = client.get("/state/current", params={"asset_id": "motor_01"})

    assert response.status_code == 404
