from pathlib import Path

import numpy as np

from ml.isolation_forest import (
    anomaly_scores,
    export_isolation_forest_to_onnx,
    train_isolation_forest,
)


def _normal_features(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(loc=[0.1, 3.0, 4.0, 1.0], scale=0.02, size=(n, 4))


def test_anomaly_scores_are_higher_for_clear_outliers() -> None:
    normal = _normal_features(100)
    model = train_isolation_forest(normal, contamination=0.05)

    outlier = np.array([[5.0, 20.0, 30.0, 15.0]])
    inlier = normal[:1]

    outlier_score = anomaly_scores(model, outlier)[0]
    inlier_score = anomaly_scores(model, inlier)[0]

    assert outlier_score > inlier_score


def test_export_isolation_forest_to_onnx_writes_a_file(tmp_path: Path) -> None:
    normal = _normal_features(50)
    model = train_isolation_forest(normal)

    output_path = tmp_path / "isolation_forest.onnx"
    export_isolation_forest_to_onnx(model, n_features=4, path=output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0
