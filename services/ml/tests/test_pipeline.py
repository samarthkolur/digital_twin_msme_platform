import json
from pathlib import Path

import pytest

from ml.datasets import DatasetNotFoundError
from ml.pipeline import pipeline_version, run_training_pipeline


def test_pipeline_version() -> None:
    assert pipeline_version() == "0.2.0"


def test_run_training_pipeline_without_allow_synthetic_raises(tmp_path: Path) -> None:
    with pytest.raises(DatasetNotFoundError):
        run_training_pipeline(
            data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", allow_synthetic=False
        )


def test_run_training_pipeline_with_synthetic_data_produces_artifacts(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"

    summary = run_training_pipeline(
        data_dir=tmp_path / "data",
        artifacts_dir=artifacts_dir,
        allow_synthetic=True,
        window_length=32,
        autoencoder_epochs=3,
    )

    assert summary.used_synthetic_data is True
    assert summary.n_training_windows == 400  # 200 normal + 200 faulty, ml.synthetic default
    assert 0.0 <= summary.isolation_forest_f1 <= 1.0
    assert 0.0 <= summary.autoencoder_f1 <= 1.0

    assert (artifacts_dir / "isolation_forest.onnx").exists()
    assert (artifacts_dir / "autoencoder.onnx").exists()
    assert (artifacts_dir / "health_index_calibration.json").exists()
    assert summary.manifest_path.exists()

    manifest = json.loads(summary.manifest_path.read_text())
    assert manifest["window_length"] == 32
    assert manifest["feature_order"] == ["rms_g", "kurtosis", "crest_factor", "peak_to_peak_g"]
    assert manifest["used_synthetic_data"] is True
    assert len(manifest["ood_bounds"]["lower"]) == 4
    assert len(manifest["ood_bounds"]["upper"]) == 4
