from pathlib import Path

import numpy as np
import onnxruntime as ort

from ml.rul import evaluate_rul, export_rul_regressor_to_onnx, predict_rul, train_rul_regressor


def _make_dataset(n: int = 200, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    features = rng.normal(size=(n, 4))
    targets = np.clip(1.0 - 0.2 * features[:, 0] + rng.normal(scale=0.05, size=n), 0.0, 1.0)
    return features, targets


def test_train_rul_regressor_fits_a_reasonable_model() -> None:
    features, targets = _make_dataset()
    model = train_rul_regressor(features, targets)

    predictions = predict_rul(model, features)
    assert predictions.shape == targets.shape
    assert predictions.min() >= 0.0
    assert predictions.max() <= 1.0


def test_predict_rul_clips_to_zero_one_range() -> None:
    features, targets = _make_dataset()
    model = train_rul_regressor(features, targets)

    # Far-out-of-distribution input should still come back clipped, not an
    # arbitrary extrapolated value outside the state object's [0, 1] framing.
    extreme_features = np.array([[100.0, 100.0, 100.0, 100.0], [-100.0, -100.0, -100.0, -100.0]])
    predictions = predict_rul(model, extreme_features)
    assert predictions.min() >= 0.0
    assert predictions.max() <= 1.0


def test_evaluate_rul_reports_reasonable_metrics_on_a_learnable_relationship() -> None:
    features, targets = _make_dataset()
    model = train_rul_regressor(features, targets)

    evaluation = evaluate_rul(model, features, targets)
    assert 0.0 <= evaluation.mae <= 1.0
    assert evaluation.r2 > 0.5  # the synthetic relationship is strongly learnable


def test_export_rul_regressor_to_onnx_produces_a_working_model(tmp_path: Path) -> None:
    features, targets = _make_dataset()
    model = train_rul_regressor(features, targets)
    onnx_path = tmp_path / "rul.onnx"

    export_rul_regressor_to_onnx(model, n_features=4, path=onnx_path)

    assert onnx_path.exists()
    session = ort.InferenceSession(str(onnx_path))
    input_name = session.get_inputs()[0].name
    onnx_predictions = session.run(None, {input_name: features[:5].astype(np.float32)})[0]
    sklearn_predictions = model.predict(features[:5])

    np.testing.assert_allclose(
        onnx_predictions.reshape(-1), sklearn_predictions, rtol=1e-4, atol=1e-4
    )
