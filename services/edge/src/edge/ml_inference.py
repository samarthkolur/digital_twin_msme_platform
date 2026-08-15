"""Optional ONNX-based ML inference (design.md §6.3, DD-031).

Loads `services/ml`'s exported training artifacts (`manifest.json` +
`isolation_forest.onnx` + `autoencoder.onnx` + `health_index_calibration.json`,
all written by `ml.pipeline.run_training_pipeline`) if present, and computes
`anomaly_score`/`health_index`/`model_confidence`/`alert_level` from a raw
vibration window + its extracted features.

If the artifacts directory doesn't exist yet (no training run has happened —
still the default state per design.md §24, since real CWRU/IMS integration
is pending), `MLInferenceEngine.load()` returns `None` rather than raising,
and those four state-object fields simply stay `null` — exactly Phase 3's
behavior before this module existed, not a startup crash.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort

from edge.providers.base import VibrationFeatures

logger = logging.getLogger("edge.ml_inference")

# design.md §6.3: "calibrated so that... <0.6 = alert threshold."
ALERT_THRESHOLD_HEALTH_INDEX = 0.6


@dataclass(frozen=True, slots=True)
class MLInferenceResult:
    anomaly_score: float
    health_index: float
    model_confidence: str  # "high" | "low" (design.md §6.0 example; "low" when OOD-flagged)
    alert_level: str  # "normal" | "alert" (design.md §6.0 example)


def _output_name_containing(session: ort.InferenceSession, hint: str) -> str:
    """skl2onnx's exact output names have varied across versions; matching by
    a case-insensitive substring instead of a hardcoded exact name is more
    robust to that than an exact-name lookup, at the cost of falling back to
    the last output if nothing matches (still deterministic, just not
    guaranteed correct — flagged here rather than silently assumed right,
    since this hasn't been exercised against a real exported model, only
    written from documented skl2onnx conventions).
    """
    outputs = session.get_outputs()
    for output in outputs:
        name: str = output.name
        if hint.lower() in name.lower():
            return name
    return str(outputs[-1].name)


class MLInferenceEngine:
    def __init__(self, artifacts_dir: Path) -> None:
        manifest = json.loads((artifacts_dir / "manifest.json").read_text())

        self._window_length: int = manifest["window_length"]
        self._feature_order: list[str] = manifest["feature_order"]
        self._ood_lower = np.array(manifest["ood_bounds"]["lower"], dtype=np.float32)
        self._ood_upper = np.array(manifest["ood_bounds"]["upper"], dtype=np.float32)

        self._if_session = ort.InferenceSession(
            str(artifacts_dir / manifest["isolation_forest_onnx"])
        )
        self._if_input_name = self._if_session.get_inputs()[0].name
        self._if_score_output_name = _output_name_containing(self._if_session, "score")

        self._ae_session = ort.InferenceSession(str(artifacts_dir / manifest["autoencoder_onnx"]))
        self._ae_input_name = self._ae_session.get_inputs()[0].name

        calibration = json.loads((artifacts_dir / manifest["health_index_calibration"]).read_text())
        self._if_baseline_mean: float = calibration["isolation_forest_baseline_mean"]
        self._if_baseline_std: float = calibration["isolation_forest_baseline_std"]
        self._ae_baseline_mean: float = calibration["reconstruction_error_baseline_mean"]
        self._ae_baseline_std: float = calibration["reconstruction_error_baseline_std"]
        self._if_weight: float = calibration["isolation_forest_weight"]
        self._ae_weight: float = calibration["reconstruction_error_weight"]
        self._std_devs_at_full_anomaly: float = calibration["std_devs_at_full_anomaly"]

    @classmethod
    def load(cls, artifacts_dir: Path) -> "MLInferenceEngine | None":
        manifest_path = artifacts_dir / "manifest.json"
        if not manifest_path.exists():
            logger.info(
                "No ML artifacts manifest at %s — anomaly_score/health_index/model_confidence/"
                "alert_level stay null until services/ml's training pipeline has run "
                "(design.md §24).",
                manifest_path,
            )
            return None
        try:
            return cls(artifacts_dir)
        except Exception:
            logger.exception(
                "Found an ML artifacts manifest at %s but failed to load it — "
                "anomaly_score/health_index/model_confidence/alert_level will stay null.",
                manifest_path,
            )
            return None

    def _normalized_anomaly(self, value: float, baseline_mean: float, baseline_std: float) -> float:
        std_devs_above_baseline = (value - baseline_mean) / baseline_std
        return float(np.clip(std_devs_above_baseline / self._std_devs_at_full_anomaly, 0.0, 1.0))

    def infer(
        self, raw_vibration_window_g: list[float], vibration: VibrationFeatures
    ) -> MLInferenceResult:
        feature_values = {
            "rms_g": vibration.rms_g,
            "kurtosis": vibration.kurtosis,
            "crest_factor": vibration.crest_factor,
            "peak_to_peak_g": vibration.peak_to_peak_g,
        }
        feature_vector = np.array(
            [[feature_values[name] for name in self._feature_order]], dtype=np.float32
        )

        if_raw_score = self._if_session.run(
            [self._if_score_output_name], {self._if_input_name: feature_vector}
        )[0]
        # skl2onnx's IsolationForest score output convention isn't pinned
        # down (see _output_name_containing) — take the first scalar out of
        # whatever shape comes back rather than assuming a fixed shape.
        isolation_forest_score = float(np.asarray(if_raw_score).reshape(-1)[0])

        window_array = np.asarray(raw_vibration_window_g, dtype=np.float32)
        window_input = (window_array - window_array.mean()).reshape(1, 1, -1)
        reconstruction = self._ae_session.run(None, {self._ae_input_name: window_input})[0]
        reconstruction_error = float(np.mean((reconstruction - window_input) ** 2))

        health_index = 1.0 - (
            self._if_weight
            * self._normalized_anomaly(
                isolation_forest_score, self._if_baseline_mean, self._if_baseline_std
            )
            + self._ae_weight
            * self._normalized_anomaly(
                reconstruction_error, self._ae_baseline_mean, self._ae_baseline_std
            )
        )
        health_index = float(np.clip(health_index, 0.0, 1.0))

        is_out_of_distribution = bool(
            np.any(feature_vector[0] < self._ood_lower)
            or np.any(feature_vector[0] > self._ood_upper)
        )

        return MLInferenceResult(
            anomaly_score=isolation_forest_score,
            health_index=health_index,
            model_confidence="low" if is_out_of_distribution else "high",
            alert_level="alert" if health_index < ALERT_THRESHOLD_HEALTH_INDEX else "normal",
        )
