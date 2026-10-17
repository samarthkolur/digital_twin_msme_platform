"""The thresholds here must stay in step with apps/dashboard/src/thresholds.ts:
the floor buzzer and the dashboard alert panel read the same state object, so
a divergence would let them disagree about whether the machine is in alert.
"""

from typing import Any

import pytest

from edge.alerting import (
    AlertThresholds,
    NullBuzzer,
    evaluate_alerts,
    get_buzzer,
    highest_level,
)

THRESHOLDS = AlertThresholds(health_index=0.6, temperature_c=70.0)


def state(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "temperature_c": 25.8,
        "health_index": None,
        "alert_level": None,
    }
    base.update(overrides)
    return base


def test_phase_1_state_raises_no_alerts() -> None:
    """Every model-derived field is null in Phase 1. A null must never be read
    as zero, which would otherwise look like a failed machine."""
    assert evaluate_alerts(state(), THRESHOLDS) == []


def test_temperature_above_threshold_warns() -> None:
    alerts = evaluate_alerts(state(temperature_c=70.1), THRESHOLDS)
    assert [a.level for a in alerts] == ["warning"]
    assert "70.1" in alerts[0].message


def test_temperature_at_threshold_does_not_warn() -> None:
    assert evaluate_alerts(state(temperature_c=70.0), THRESHOLDS) == []


def test_health_index_below_threshold_warns() -> None:
    alerts = evaluate_alerts(state(health_index=0.55), THRESHOLDS)
    assert [a.level for a in alerts] == ["warning"]


def test_health_index_far_below_threshold_is_critical() -> None:
    # 0.6 * 0.75 = 0.45; anything under that is critical, not a warning.
    alerts = evaluate_alerts(state(health_index=0.44), THRESHOLDS)
    assert [a.level for a in alerts] == ["critical"]


def test_critical_fraction_comes_from_the_thresholds() -> None:
    """0.40 is critical at the default 0.75 fraction (0.45 cut-off) but only a
    warning once the configured fraction lowers the cut-off to 0.30."""
    default = evaluate_alerts(state(health_index=0.40), THRESHOLDS)
    configured = evaluate_alerts(
        state(health_index=0.40),
        AlertThresholds(health_index=0.6, temperature_c=70.0, critical_fraction=0.5),
    )
    assert [a.level for a in default] == ["critical"]
    assert [a.level for a in configured] == ["warning"]


def test_model_alert_level_is_surfaced_alongside_thresholds() -> None:
    alerts = evaluate_alerts(state(temperature_c=75.0, alert_level="critical"), THRESHOLDS)
    assert {a.level for a in alerts} == {"warning", "critical"}
    assert len(alerts) == 2, "model alert must not replace the threshold alert"


def test_normal_model_alert_level_is_not_an_alert() -> None:
    assert evaluate_alerts(state(alert_level="normal"), THRESHOLDS) == []


def test_highest_level_prefers_critical() -> None:
    alerts = evaluate_alerts(state(temperature_c=75.0, health_index=0.1), THRESHOLDS)
    assert highest_level(alerts) == "critical"
    assert highest_level([]) is None


def test_default_buzzer_is_silent_and_closeable() -> None:
    buzzer = get_buzzer("none", 18)
    assert isinstance(buzzer, NullBuzzer)
    buzzer.signal("critical")  # must not raise on a machine with no GPIO
    buzzer.close()


def test_unknown_buzzer_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown buzzer"):
        get_buzzer("piezo", 18)
