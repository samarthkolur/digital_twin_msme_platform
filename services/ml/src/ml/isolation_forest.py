"""Isolation Forest anomaly-score baseline (design.md §6.3 step 1)."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from skl2onnx import to_onnx
from skl2onnx.common.data_types import FloatTensorType
from sklearn.ensemble import IsolationForest


def train_isolation_forest(
    features: NDArray[np.float64],
    contamination: float = 0.1,
    random_state: int = 0,
) -> IsolationForest:
    """Trains on the (n_windows, 4) feature matrix from
    `ml.features.features_to_array` (rms/kurtosis/crest_factor/
    peak_to_peak columns, design.md §6.3). `contamination` should be tuned
    against the real CWRU normal-class windows once available (§24); the
    default here is sklearn's own default, not a calibrated value.
    """
    model = IsolationForest(contamination=contamination, random_state=random_state)
    model.fit(features)
    return model


def anomaly_scores(model: IsolationForest, features: NDArray[np.float64]) -> NDArray[np.float64]:
    """Higher = more anomalous (sklearn's own `score_samples` is inverted —
    more negative means more anomalous — so this flips the sign for a more
    intuitive "higher score = worse" convention matching `ml.health_index`).
    """
    scores: NDArray[np.float64] = -model.score_samples(features)
    return scores


def export_isolation_forest_to_onnx(model: IsolationForest, n_features: int, path: Path) -> None:
    """Exports to ONNX (design.md DD-031: ONNX replaces the originally
    documented TFLite target — see the DD for why) via skl2onnx, so `edge`
    can run inference through a single onnxruntime session shared with the
    autoencoder rather than needing a second, sklearn-specific runtime.
    """
    onnx_model = to_onnx(
        model,
        initial_types=[("input", FloatTensorType([None, n_features]))],
        # skl2onnx 1.20's IsolationForest converter emits ai.onnx.ml ops
        # tagged opset 4, but the same library's own opset table caps
        # ai.onnx.ml support at 3 — pinning target_opset explicitly avoids
        # the internal mismatch (verified against skl2onnx 1.20 / onnx 1.22).
        target_opset={"ai.onnx.ml": 3, "": 18},
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(onnx_model.SerializeToString())
