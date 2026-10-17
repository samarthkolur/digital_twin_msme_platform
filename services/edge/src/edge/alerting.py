"""Threshold evaluation and the audible (GPIO buzzer) alert path.

The threshold rules here deliberately mirror the dashboard's
`apps/dashboard/src/thresholds.ts` so the floor buzzer and the on-screen
alert panel can never disagree about whether a state object is in alert.
Both read the same state object (design.md §6.0) and both surface the
model's own `alert_level` alongside the threshold checks rather than
letting either mask the other.

The buzzer follows the `SensorProvider` pattern (DD-003): a protocol with a
real GPIO implementation and a no-op default, selected by an environment
variable, so app code never imports `RPi.GPIO` on a machine that has no
GPIO (dev laptops, CI containers).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Literal, Protocol

logger = logging.getLogger("edge.alerting")

# Matches DEFAULT_HEALTH_INDEX_ALERT_THRESHOLD / DEFAULT_TEMPERATURE_ALERT_THRESHOLD_C
# in apps/dashboard/src/thresholds.ts. The temperature value has no
# pilot-machine calibration yet (design.md §24) — it is an operator-overridable
# placeholder, not a calibrated figure.
DEFAULT_HEALTH_INDEX_THRESHOLD = 0.6
DEFAULT_TEMPERATURE_THRESHOLD_C = 70.0

# A health index below this fraction of the threshold is critical rather than
# a warning, matching the dashboard's `thresholds.healthIndex * 0.75`.
CRITICAL_HEALTH_FRACTION = 0.75

AlertLevel = Literal["warning", "critical"]


@dataclass(frozen=True)
class AlertThresholds:
    health_index: float = DEFAULT_HEALTH_INDEX_THRESHOLD
    temperature_c: float = DEFAULT_TEMPERATURE_THRESHOLD_C


@dataclass(frozen=True)
class Alert:
    level: AlertLevel
    message: str


def evaluate_alerts(state: dict[str, Any], thresholds: AlertThresholds) -> list[Alert]:
    """Evaluates the configurable thresholds against one state object.

    Mirrors `evaluateAlerts` in apps/dashboard/src/thresholds.ts. Fields the
    ML pipeline has not populated yet are null in Phase 1 and are skipped
    rather than treated as zero, so an absent model output never reads as a
    healthy machine.
    """
    alerts: list[Alert] = []

    health_index = state.get("health_index")
    if health_index is not None and health_index < thresholds.health_index:
        critical = health_index < thresholds.health_index * CRITICAL_HEALTH_FRACTION
        alerts.append(
            Alert(
                level="critical" if critical else "warning",
                message=(
                    f"Health index {health_index:.2f} is below the "
                    f"{thresholds.health_index:.2f} alert threshold"
                ),
            )
        )

    temperature_c = state.get("temperature_c")
    if temperature_c is not None and temperature_c > thresholds.temperature_c:
        alerts.append(
            Alert(
                level="warning",
                message=(
                    f"Temperature {temperature_c}°C exceeds the "
                    f"{thresholds.temperature_c}°C threshold"
                ),
            )
        )

    alert_level = state.get("alert_level")
    if alert_level is not None and alert_level != "normal":
        alerts.append(
            Alert(
                level="critical" if alert_level == "critical" else "warning",
                message=f"Model-reported alert level: {alert_level}",
            )
        )

    return alerts


def highest_level(alerts: list[Alert]) -> AlertLevel | None:
    if any(a.level == "critical" for a in alerts):
        return "critical"
    if alerts:
        return "warning"
    return None


class Buzzer(Protocol):
    """Audible alert output. `signal` is synchronous and short; callers on an
    event loop should dispatch it via `asyncio.to_thread`."""

    def signal(self, level: AlertLevel) -> None: ...

    def close(self) -> None: ...


class NullBuzzer:
    """Default: records the intent and makes no sound. Used on dev machines,
    in CI, and wherever no buzzer is fitted."""

    def signal(self, level: AlertLevel) -> None:
        logger.info("buzzer (not fitted): would sound %s pattern", level)

    def close(self) -> None:
        return None


class GpioBuzzer:
    """Drives a piezo buzzer on a BCM-numbered GPIO pin.

    One short beep for a warning, three for a critical alert, so the floor can
    tell them apart without looking at the dashboard. The pin is driven high
    and low directly, which suits an active buzzer; a passive element needs a
    PWM carrier instead. Drive the element through a transistor rather than
    off the pin: GPIO is rated 16 mA and piezos commonly draw more.
    """

    _WARNING_BEEPS = 1
    _CRITICAL_BEEPS = 3
    _BEEP_SECONDS = 0.12
    _GAP_SECONDS = 0.10

    def __init__(self, pin: int) -> None:
        import RPi.GPIO as GPIO  # Pi-only; imported lazily like the hardware provider

        self._gpio = GPIO
        self._pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        logger.info("buzzer ready on BCM pin %d", pin)

    def signal(self, level: AlertLevel) -> None:
        beeps = self._CRITICAL_BEEPS if level == "critical" else self._WARNING_BEEPS
        for index in range(beeps):
            self._gpio.output(self._pin, self._gpio.HIGH)
            time.sleep(self._BEEP_SECONDS)
            self._gpio.output(self._pin, self._gpio.LOW)
            if index < beeps - 1:
                time.sleep(self._GAP_SECONDS)

    def close(self) -> None:
        try:
            self._gpio.output(self._pin, self._gpio.LOW)
            self._gpio.cleanup(self._pin)
        except Exception:  # pragma: no cover - teardown must never raise
            logger.warning("buzzer cleanup failed", exc_info=True)


def get_buzzer(name: str, pin: int) -> Buzzer:
    if name in ("none", "null", ""):
        return NullBuzzer()
    if name == "gpio":
        return GpioBuzzer(pin)
    raise ValueError(f"Unknown buzzer: {name!r}")
