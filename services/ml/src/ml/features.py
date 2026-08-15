"""Statistical vibration feature extraction for ML training.

Independent re-implementation of the same four features
`services/edge/src/edge/features.py` computes at inference time (RMS,
kurtosis, crest factor, peak-to-peak) — `edge` and `ml` are separate `uv`
projects with no shared Python package (design.md DD-002/§14), so this is a
deliberate duplication, not drift, matching DD-026's precedent for
edge/api's `state_history` schema.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class WindowFeatures:
    rms_g: float
    kurtosis: float
    crest_factor: float
    peak_to_peak_g: float


def compute_window_features(window: NDArray[np.float64]) -> WindowFeatures:
    """Computes RMS/kurtosis/crest-factor/peak-to-peak over a 1D vibration
    window, after removing the window's mean (the static offset — gravity at
    the sensor's mount orientation on real hardware; an arbitrary DC term in
    synthetic/dataset windows) so all four features describe the dynamic
    (AC-coupled) signal, matching `edge.features.compute_vibration_features`.
    """
    ac = window - window.mean()
    variance = float(np.mean(ac**2))
    rms_g = float(np.sqrt(variance))
    kurtosis = float(np.mean(ac**4) / variance**2) if variance > 0 else 0.0
    peak_to_peak_g = float(ac.max() - ac.min())
    crest_factor = float(np.max(np.abs(ac)) / rms_g) if rms_g > 0 else 0.0

    return WindowFeatures(
        rms_g=round(rms_g, 4),
        kurtosis=round(kurtosis, 3),
        crest_factor=round(crest_factor, 3),
        peak_to_peak_g=round(peak_to_peak_g, 4),
    )


def features_to_array(features: list[WindowFeatures]) -> NDArray[np.float64]:
    """Stacks a list of per-window features into an (n_windows, 4) matrix,
    in the fixed column order (rms, kurtosis, crest_factor, peak_to_peak)
    that every downstream model (Isolation Forest, OOD detector) assumes.
    """
    return np.array(
        [[f.rms_g, f.kurtosis, f.crest_factor, f.peak_to_peak_g] for f in features],
        dtype=np.float64,
    )
