"""Evaluation helpers matching design.md §9's targets.

F1 targets (Isolation Forest >= 0.80, autoencoder >= 0.85) are defined
against a held-out *CWRU* test set — real dataset not yet integrated (§24).
`evaluate_f1` itself is dataset-agnostic; `ml.pipeline` currently calls it
against synthetic labeled data only, and any number it reports is explicitly
not the §9 metric until it's run against real CWRU data.
"""

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import f1_score


def scores_to_binary_predictions(
    scores: NDArray[np.float64], threshold: float
) -> NDArray[np.int64]:
    """Anomaly scores (higher = more anomalous) -> 0/1 predictions at a
    chosen threshold, matching `ml.synthetic`'s 0=normal/1=faulty convention.
    """
    return (scores > threshold).astype(np.int64)


def evaluate_f1(y_true: NDArray[np.int64], y_pred: NDArray[np.int64]) -> float:
    return float(f1_score(y_true, y_pred, zero_division=0))
