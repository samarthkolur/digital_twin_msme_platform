"""Health index calibration (design.md §6.3 step 3).

"A normalized scalar (0.0-1.0)... computed from reconstruction error and
Isolation Forest anomaly score using a weighted linear combination,
calibrated so that 1.0 = normal baseline and <0.6 = alert threshold."

Calibration fits each signal's normal-baseline mean/std (design.md's
"30-minute normal-operation recording") and maps a configurable number of
baseline standard deviations above that mean onto a full 0->1 anomaly
contribution, so `k` is the calibration's actual sensitivity knob — the
health index isn't 1.0 only at the exact baseline mean, it stays high across
the normal range and only degrades once a reading is `k` standard deviations
past what the baseline recording showed.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class HealthIndexCalibration:
    isolation_forest_baseline_mean: float
    isolation_forest_baseline_std: float
    reconstruction_error_baseline_mean: float
    reconstruction_error_baseline_std: float
    isolation_forest_weight: float = 0.5
    reconstruction_error_weight: float = 0.5
    std_devs_at_full_anomaly: float = 4.0

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def from_json(cls, path: Path) -> "HealthIndexCalibration":
        return cls(**json.loads(path.read_text()))


def calibrate_health_index(
    baseline_isolation_forest_scores: NDArray[np.float64],
    baseline_reconstruction_errors: NDArray[np.float64],
    isolation_forest_weight: float = 0.5,
    reconstruction_error_weight: float = 0.5,
    std_devs_at_full_anomaly: float = 4.0,
) -> HealthIndexCalibration:
    """Fits calibration stats from normal-baseline Isolation Forest scores
    and autoencoder reconstruction errors (both computed by the caller over
    the same baseline recording, design.md §6.3).
    """
    if_std = float(np.std(baseline_isolation_forest_scores))
    ae_std = float(np.std(baseline_reconstruction_errors))
    return HealthIndexCalibration(
        isolation_forest_baseline_mean=float(np.mean(baseline_isolation_forest_scores)),
        isolation_forest_baseline_std=if_std if if_std > 0 else 1.0,
        reconstruction_error_baseline_mean=float(np.mean(baseline_reconstruction_errors)),
        reconstruction_error_baseline_std=ae_std if ae_std > 0 else 1.0,
        isolation_forest_weight=isolation_forest_weight,
        reconstruction_error_weight=reconstruction_error_weight,
        std_devs_at_full_anomaly=std_devs_at_full_anomaly,
    )


def _normalized_anomaly(value: float, baseline_mean: float, baseline_std: float, k: float) -> float:
    std_devs_above_baseline = (value - baseline_mean) / baseline_std
    return float(np.clip(std_devs_above_baseline / k, 0.0, 1.0))


def compute_health_index(
    isolation_forest_score: float,
    reconstruction_error: float,
    calibration: HealthIndexCalibration,
) -> float:
    normalized_if = _normalized_anomaly(
        isolation_forest_score,
        calibration.isolation_forest_baseline_mean,
        calibration.isolation_forest_baseline_std,
        calibration.std_devs_at_full_anomaly,
    )
    normalized_ae = _normalized_anomaly(
        reconstruction_error,
        calibration.reconstruction_error_baseline_mean,
        calibration.reconstruction_error_baseline_std,
        calibration.std_devs_at_full_anomaly,
    )
    weighted_anomaly = (
        calibration.isolation_forest_weight * normalized_if
        + calibration.reconstruction_error_weight * normalized_ae
    )
    return float(np.clip(1.0 - weighted_anomaly, 0.0, 1.0))
