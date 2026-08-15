"""Synthetic vibration data for pipeline development and tests.

design.md §6.3 specifies the CWRU and IMS Bearing datasets as the real
training data source; neither is downloaded into this repo yet (§18
External Integrations: "Planned (Phase 4)... Not yet integrated" — real
dataset acquisition is a standing Pending Task, §24). This module generates
plausible normal/faulty vibration windows so the rest of the pipeline
(feature extraction, Isolation Forest, autoencoder, OOD flagging, health
index, ONNX export) can be built and exercised end-to-end without real data,
exactly as `services/edge/src/edge/providers/simulated.py` does for the edge
service. Models trained on this data are placeholders, not calibrated
detectors — see design.md DD-031.
"""

import numpy as np
from numpy.typing import NDArray


def generate_normal_window(length: int, rng: np.random.Generator) -> NDArray[np.float64]:
    """A roughly-Gaussian AC-coupled window plus a small DC offset, mimicking
    baseline (healthy) vibration noise around design.md §6.0's example
    kurtosis (~3.0, i.e. Gaussian-like) rather than a specific waveform.
    """
    dc_offset = 1.0  # arbitrary static component, analogous to gravity offset on real hardware
    return dc_offset + rng.normal(loc=0.0, scale=0.08, size=length)


def generate_faulty_window(length: int, rng: np.random.Generator) -> NDArray[np.float64]:
    """A window with impulsive spikes layered on the normal baseline —
    qualitatively similar to a bearing-fault signature (elevated RMS,
    kurtosis, crest factor) without claiming to model any specific real
    fault mechanism.
    """
    window = generate_normal_window(length, rng) * 2.5
    n_spikes = max(1, length // 40)
    spike_indices = rng.integers(0, length, size=n_spikes)
    window[spike_indices] += rng.normal(loc=0.0, scale=1.2, size=n_spikes)
    return window


def generate_labeled_dataset(
    n_normal: int,
    n_faulty: int,
    window_length: int,
    seed: int = 0,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Returns (windows, labels) with labels 0=normal, 1=faulty — the
    convention `ml.evaluate` and the Isolation Forest/autoencoder training
    functions assume throughout this package.
    """
    rng = np.random.default_rng(seed)
    normal = np.stack([generate_normal_window(window_length, rng) for _ in range(n_normal)])
    faulty = np.stack([generate_faulty_window(window_length, rng) for _ in range(n_faulty)])

    windows = np.concatenate([normal, faulty], axis=0)
    labels = np.concatenate([np.zeros(n_normal, dtype=np.int64), np.ones(n_faulty, dtype=np.int64)])
    return windows, labels
