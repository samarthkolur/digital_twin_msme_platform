import importlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import appconfig.main


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "config.sqlite3"))
    monkeypatch.delenv("ENABLE_PHASE2", raising=False)
    monkeypatch.delenv("COPILOT_LLM_MODE", raising=False)
    importlib.reload(appconfig.main)
    with TestClient(appconfig.main.app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_get_config_uses_camel_case_and_phase1_default(client: TestClient) -> None:
    body = client.get("/config").json()
    assert body == {
        "enablePhase2": False,
        "publishIntervalSeconds": 5.0,
        "alertHealthIndex": 0.6,
        "alertTemperatureC": 70.0,
        "alertCriticalFraction": 0.75,
        "copilotLlmMode": "local",
        "copilotStaleAfterSeconds": 300,
        "copilotContextSize": 10,
    }


def test_patch_updates_only_given_fields(client: TestClient) -> None:
    response = client.patch("/config", json={"enablePhase2": True})
    assert response.status_code == 200
    assert response.json()["enablePhase2"] is True
    assert response.json()["alertTemperatureC"] == 70.0
    assert client.get("/config").json()["enablePhase2"] is True


def test_patch_rejects_invalid_values(client: TestClient) -> None:
    assert client.patch("/config", json={"alertHealthIndex": 2}).status_code == 422
    assert client.patch("/config", json={"bogus": 1}).status_code == 422
    assert client.get("/config").json()["alertHealthIndex"] == 0.6


def test_patch_validates_the_copilot_settings(client: TestClient) -> None:
    ok = client.patch("/config", json={"copilotLlmMode": "api", "copilotContextSize": 25})
    assert ok.status_code == 200
    assert ok.json()["copilotLlmMode"] == "api"
    assert ok.json()["copilotContextSize"] == 25
    assert client.patch("/config", json={"copilotLlmMode": "cloud"}).status_code == 422
    assert client.patch("/config", json={"copilotStaleAfterSeconds": 5}).status_code == 422
    assert client.patch("/config", json={"alertCriticalFraction": 0}).status_code == 422
