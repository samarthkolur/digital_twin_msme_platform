import json
from pathlib import Path

import pytest

from appconfig.cli import main


@pytest.fixture(autouse=True)
def _database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "config.sqlite3"))
    monkeypatch.delenv("ENABLE_PHASE2", raising=False)


def test_profiles_empty_when_phase2_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["profiles"]) == 0
    assert capsys.readouterr().out.strip() == ""


def test_set_then_profiles_reports_phase2(capsys: pytest.CaptureFixture[str]) -> None:
    main(["set", "enablePhase2", "true"])
    capsys.readouterr()
    main(["profiles"])
    assert capsys.readouterr().out.strip() == "phase2"


def test_show_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    main(["set", "alertTemperatureC", "65"])
    capsys.readouterr()
    main(["show"])
    assert json.loads(capsys.readouterr().out)["alertTemperatureC"] == 65
