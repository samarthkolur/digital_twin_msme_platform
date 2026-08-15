import numpy as np

from ml.features import compute_window_features, features_to_array


def test_compute_window_features_matches_hand_computation() -> None:
    # Same hand-computed case as services/edge/tests/test_features.py, so the
    # two independent implementations (DD-002) are cross-checked against the
    # same known values.
    window = np.array([1.0, 1.0, 1.0, 2.0])

    features = compute_window_features(window)

    assert abs(features.rms_g - 0.4330) < 1e-4
    assert abs(features.kurtosis - 7 / 3) < 1e-3
    assert abs(features.peak_to_peak_g - 1.0) < 1e-4
    assert abs(features.crest_factor - 3**0.5) < 1e-3


def test_compute_window_features_handles_zero_variance() -> None:
    window = np.array([1.0, 1.0, 1.0, 1.0])

    features = compute_window_features(window)

    assert features.rms_g == 0.0
    assert features.kurtosis == 0.0
    assert features.crest_factor == 0.0
    assert features.peak_to_peak_g == 0.0


def test_features_to_array_preserves_column_order() -> None:
    window = np.array([1.0, 1.0, 1.0, 2.0])
    features = compute_window_features(window)

    matrix = features_to_array([features])

    assert matrix.shape == (1, 4)
    assert matrix[0, 0] == features.rms_g
    assert matrix[0, 1] == features.kurtosis
    assert matrix[0, 2] == features.crest_factor
    assert matrix[0, 3] == features.peak_to_peak_g
