import json
from pathlib import Path

import onnx
from onnx import TensorProto, helper

from edge.ml_inference import MLInferenceEngine
from edge.providers.base import VibrationFeatures

FEATURE_ORDER = ["rms_g", "kurtosis", "crest_factor", "peak_to_peak_g"]


def _build_sum_scores_model(path: Path) -> None:
    """A stub "isolation forest" ONNX model: output "scores" = sum of the 4
    input features. Deterministic and hand-verifiable, standing in for a
    real skl2onnx-exported IsolationForest without needing sklearn/skl2onnx
    as an edge test dependency (edge/ml stay independent services, DD-002).
    """
    input_tensor = helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, 4])
    output_tensor = helper.make_tensor_value_info("scores", TensorProto.FLOAT, [None, 1])
    node = helper.make_node("ReduceSum", inputs=["input"], outputs=["scores"], axes=[1], keepdims=1)
    graph = helper.make_graph([node], "isolation_forest_stub", [input_tensor], [output_tensor])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 11)])
    onnx.save(model, str(path))


def _build_identity_autoencoder_model(path: Path) -> None:
    """A stub autoencoder ONNX model that reconstructs its input exactly
    (reconstruction error is always 0), standing in for a real torch-exported
    Conv1DAutoencoder.
    """
    input_tensor = helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, 1, None])
    output_tensor = helper.make_tensor_value_info(
        "reconstruction", TensorProto.FLOAT, [None, 1, None]
    )
    node = helper.make_node("Identity", inputs=["input"], outputs=["reconstruction"])
    graph = helper.make_graph([node], "autoencoder_stub", [input_tensor], [output_tensor])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 11)])
    onnx.save(model, str(path))


def _write_artifacts(artifacts_dir: Path) -> None:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    _build_sum_scores_model(artifacts_dir / "isolation_forest.onnx")
    _build_identity_autoencoder_model(artifacts_dir / "autoencoder.onnx")

    (artifacts_dir / "health_index_calibration.json").write_text(
        json.dumps(
            {
                "isolation_forest_baseline_mean": 4.0,
                "isolation_forest_baseline_std": 1.0,
                "reconstruction_error_baseline_mean": 0.0,
                "reconstruction_error_baseline_std": 1.0,
                "isolation_forest_weight": 0.5,
                "reconstruction_error_weight": 0.5,
                "std_devs_at_full_anomaly": 4.0,
            }
        )
    )
    (artifacts_dir / "manifest.json").write_text(
        json.dumps(
            {
                "window_length": 4,
                "feature_order": FEATURE_ORDER,
                "isolation_forest_onnx": "isolation_forest.onnx",
                "autoencoder_onnx": "autoencoder.onnx",
                "health_index_calibration": "health_index_calibration.json",
                "ood_bounds": {"lower": [0.0, 0.0, 0.0, 0.0], "upper": [10.0, 10.0, 10.0, 10.0]},
                "isolation_forest_f1": 0.9,
                "autoencoder_f1": 0.9,
                "used_synthetic_data": True,
            }
        )
    )


def test_load_returns_none_when_no_manifest_present(tmp_path: Path) -> None:
    assert MLInferenceEngine.load(tmp_path) is None


def test_infer_at_baseline_yields_health_index_near_1(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    engine = MLInferenceEngine.load(tmp_path)
    assert engine is not None

    # rms+kurtosis+crest_factor+peak_to_peak = 4.0, matching the calibration's
    # isolation_forest_baseline_mean exactly.
    vibration = VibrationFeatures(
        rms_g=1.0, kurtosis=1.0, crest_factor=1.0, peak_to_peak_g=1.0, sampling_hz=3200
    )
    result = engine.infer([1.0, 1.0, 1.0, 1.0], vibration)

    assert result.anomaly_score == 4.0
    assert result.health_index == 1.0
    assert result.model_confidence == "high"
    assert result.alert_level == "normal"


def test_infer_with_elevated_features_flags_ood_and_low_health_index(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    engine = MLInferenceEngine.load(tmp_path)
    assert engine is not None

    # sum = 80, far above the OOD upper bound (10 per feature) and the
    # isolation_forest_baseline_mean (4.0).
    vibration = VibrationFeatures(
        rms_g=20.0, kurtosis=20.0, crest_factor=20.0, peak_to_peak_g=20.0, sampling_hz=3200
    )
    result = engine.infer([1.0, 1.0, 1.0, 1.0], vibration)

    assert result.anomaly_score == 80.0
    assert result.health_index < 0.6
    assert result.model_confidence == "low"
    assert result.alert_level == "alert"
