"""Remaining-useful-life (RUL) regression (design.md §6.3, DD-040).

Predicts a normalized "life fraction remaining" (1.0 = start of life, 0.0 =
at/near failure) from the same four statistical vibration features
Isolation Forest already computes (`ml.features.compute_window_features`) —
not a new feature set, so `edge` can run RUL inference on the exact feature
vector it already builds per reading, at effectively no extra cost.

A linear `Ridge` regressor, not a neural net: the deployment target is a
Raspberry Pi 4 (design.md §6.2) sharing CPU with four other containers, so
the point of this model is to be genuinely tiny (a handful of floats) and
near-instant to run — the same reasoning DD-031 already applied when scoping
Isolation Forest and the autoencoder's window length. A held-out evaluation
(train/test split by *source file*, not by window — see
`ml.ims_loader.load_ims_rul_windows`) is used from the start here, unlike
the pre-existing Isolation Forest/autoencoder F1 self-evaluation gap tracked
in design.md §26 as separate technical debt.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from skl2onnx import to_onnx
from skl2onnx.common.data_types import FloatTensorType
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score


@dataclass(frozen=True, slots=True)
class RulEvaluation:
    mae: float
    r2: float


def train_rul_regressor(
    features: NDArray[np.float64],
    targets: NDArray[np.float64],
    alpha: float = 1.0,
    random_state: int = 0,
) -> Ridge:
    model = Ridge(alpha=alpha, random_state=random_state)
    model.fit(features, targets)
    return model


def predict_rul(model: Ridge, features: NDArray[np.float64]) -> NDArray[np.float64]:
    """Clipped to [0, 1]: the target is a fraction, but an unregularized
    linear model can extrapolate outside that range for out-of-distribution
    inputs — matches the state object's own [0, 1] framing (design.md §6.0).
    """
    predictions: NDArray[np.float64] = np.clip(model.predict(features), 0.0, 1.0)
    return predictions


def evaluate_rul(
    model: Ridge, features: NDArray[np.float64], targets: NDArray[np.float64]
) -> RulEvaluation:
    predictions = predict_rul(model, features)
    return RulEvaluation(
        mae=float(mean_absolute_error(targets, predictions)),
        r2=float(r2_score(targets, predictions)),
    )


def export_rul_regressor_to_onnx(model: Ridge, n_features: int, path: Path) -> None:
    onnx_model = to_onnx(model, initial_types=[("input", FloatTensorType([None, n_features]))])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(onnx_model.SerializeToString())
