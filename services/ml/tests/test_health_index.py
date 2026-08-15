from pathlib import Path

import numpy as np

from ml.health_index import calibrate_health_index, compute_health_index


def _baseline() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    if_scores = rng.normal(loc=0.0, scale=0.1, size=200)
    recon_errors = rng.normal(loc=0.01, scale=0.002, size=200)
    return if_scores, recon_errors


def test_health_index_is_near_1_at_the_baseline_mean() -> None:
    if_scores, recon_errors = _baseline()
    calibration = calibrate_health_index(if_scores, recon_errors)

    index = compute_health_index(
        isolation_forest_score=float(if_scores.mean()),
        reconstruction_error=float(recon_errors.mean()),
        calibration=calibration,
    )

    assert index > 0.95


def test_health_index_drops_well_below_threshold_for_a_clear_anomaly() -> None:
    if_scores, recon_errors = _baseline()
    calibration = calibrate_health_index(if_scores, recon_errors)

    # far beyond std_devs_at_full_anomaly (default 4) past the baseline mean
    index = compute_health_index(
        isolation_forest_score=float(if_scores.mean() + 10 * if_scores.std()),
        reconstruction_error=float(recon_errors.mean() + 10 * recon_errors.std()),
        calibration=calibration,
    )

    assert index < 0.1


def test_health_index_stays_within_0_and_1() -> None:
    if_scores, recon_errors = _baseline()
    calibration = calibrate_health_index(if_scores, recon_errors)

    extreme = compute_health_index(
        isolation_forest_score=-1000.0, reconstruction_error=-1000.0, calibration=calibration
    )
    assert 0.0 <= extreme <= 1.0


def test_calibration_round_trips_through_json(tmp_path: Path) -> None:
    if_scores, recon_errors = _baseline()
    calibration = calibrate_health_index(if_scores, recon_errors)

    path = tmp_path / "calibration.json"
    calibration.to_json(path)
    loaded = calibration.from_json(path)

    assert loaded == calibration
