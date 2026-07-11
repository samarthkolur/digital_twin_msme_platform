import pytest

from edge.features import compute_vibration_features


def test_compute_vibration_features_matches_hand_computation() -> None:
    # magnitudes = [1.0, 1.0, 1.0, 2.0]; mean = 1.25; AC = [-0.25, -0.25, -0.25, 0.75]
    # variance = mean(AC^2) = 0.1875 => rms = sqrt(0.1875) = 0.4330127...
    # 4th moment = mean(AC^4) = 0.08203125 => kurtosis = 0.08203125 / 0.1875^2 = 7/3
    # peak-to-peak = 0.75 - (-0.25) = 1.0
    # crest_factor = max(|AC|) / rms = 0.75 / 0.4330127... = sqrt(3)
    features = compute_vibration_features([1.0, 1.0, 1.0, 2.0], sampling_hz=3200)

    assert features.rms_g == pytest.approx(0.4330, abs=1e-4)
    assert features.kurtosis == pytest.approx(7 / 3, abs=1e-3)
    assert features.peak_to_peak_g == pytest.approx(1.0, abs=1e-4)
    assert features.crest_factor == pytest.approx(3**0.5, abs=1e-3)
    assert features.sampling_hz == 3200


def test_compute_vibration_features_handles_zero_variance() -> None:
    features = compute_vibration_features([1.0, 1.0, 1.0, 1.0], sampling_hz=800)

    assert features.rms_g == 0.0
    assert features.kurtosis == 0.0
    assert features.crest_factor == 0.0
    assert features.peak_to_peak_g == 0.0
