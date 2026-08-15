"""Training pipeline entry point (design.md §6.3, §10 Phase 4).

Orchestrates: dataset loading (real CWRU/IMS if present, or an explicit
synthetic placeholder — see `ml.datasets`/`ml.synthetic`), feature
extraction, Isolation Forest baseline training, 1D conv autoencoder
training, OOD-bounds fitting, health-index calibration, F1 evaluation, and
ONNX export (design.md DD-031) of both models plus a `manifest.json` into
`artifacts_dir`, for `services/edge` to load (see `edge.ml_inference`, wired
in the same session — design.md §28 Entry 13).
"""

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from ml.autoencoder import export_autoencoder_to_onnx, reconstruction_error, train_autoencoder
from ml.datasets import DEFAULT_DATA_DIR, DatasetNotFoundError, cwru_data_dir
from ml.evaluate import evaluate_f1, scores_to_binary_predictions
from ml.features import compute_window_features, features_to_array
from ml.health_index import calibrate_health_index
from ml.isolation_forest import (
    anomaly_scores,
    export_isolation_forest_to_onnx,
    train_isolation_forest,
)
from ml.ood import fit_ood_bounds
from ml.synthetic import generate_labeled_dataset

logger = logging.getLogger("ml.pipeline")

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"

# Matches services/edge/src/edge/providers/hardware.py's `_SAMPLE_COUNT`
# (DD-022): edge currently reads a 64-sample magnitude burst per `read()`
# call, not a continuous 3,200 Hz stream. Training windows the same length
# let the exported autoencoder consume edge's raw burst directly, without
# requiring edge to buffer multiple reads into a longer window first.
DEFAULT_WINDOW_LENGTH = 64

FEATURE_ORDER = ["rms_g", "kurtosis", "crest_factor", "peak_to_peak_g"]


def pipeline_version() -> str:
    return "0.2.0"


@dataclass(frozen=True, slots=True)
class TrainingSummary:
    used_synthetic_data: bool
    n_training_windows: int
    isolation_forest_f1: float
    autoencoder_f1: float
    manifest_path: Path


def _load_training_windows(
    data_dir: Path, allow_synthetic: bool, window_length: int, synthetic_seed: int
) -> tuple[NDArray[np.float64], NDArray[np.int64], bool]:
    """Returns (windows, labels [0=normal, 1=faulty], used_synthetic)."""
    try:
        cwru_data_dir(data_dir)
    except DatasetNotFoundError:
        if not allow_synthetic:
            raise
        logger.warning(
            "Real CWRU dataset not found at %s — training on synthetic placeholder data "
            "instead (design.md DD-031). These models are NOT calibrated detectors.",
            data_dir,
        )
        windows, labels = generate_labeled_dataset(
            n_normal=200, n_faulty=200, window_length=window_length, seed=synthetic_seed
        )
        return windows, labels, True

    # cwru_data_dir() found real files but real CWRU parsing isn't built yet
    # (design.md §24 Pending Tasks) — fail loudly rather than silently
    # falling back to synthetic data when real data is actually present.
    raise NotImplementedError(
        "Real CWRU/IMS preprocessing is not yet implemented (design.md §24) — only the "
        "synthetic-data path (allow_synthetic=True) currently works."
    )


def run_training_pipeline(
    data_dir: Path = DEFAULT_DATA_DIR,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
    allow_synthetic: bool = False,
    window_length: int = DEFAULT_WINDOW_LENGTH,
    autoencoder_epochs: int = 20,
    synthetic_seed: int = 0,
) -> TrainingSummary:
    windows, labels, used_synthetic = _load_training_windows(
        data_dir, allow_synthetic, window_length, synthetic_seed
    )
    normal_mask = labels == 0
    normal_windows = windows[normal_mask]

    window_features = [compute_window_features(w) for w in windows]
    feature_matrix = features_to_array(window_features)
    normal_feature_matrix = feature_matrix[normal_mask]

    isolation_forest = train_isolation_forest(normal_feature_matrix)
    if_scores_all = anomaly_scores(isolation_forest, feature_matrix)
    if_scores_normal = if_scores_all[normal_mask]

    autoencoder = train_autoencoder(normal_windows, epochs=autoencoder_epochs, seed=synthetic_seed)
    recon_errors_all = reconstruction_error(autoencoder, windows)
    recon_errors_normal = recon_errors_all[normal_mask]

    ood_bounds = fit_ood_bounds(normal_feature_matrix)
    calibration = calibrate_health_index(if_scores_normal, recon_errors_normal)

    # 99th percentile of the *normal* distribution as the anomaly-score
    # threshold for the F1 evaluation below — consistent with the OOD
    # bounds' use of the normal distribution's own spread as "expected".
    if_threshold = float(np.percentile(if_scores_normal, 99))
    ae_threshold = float(np.percentile(recon_errors_normal, 99))
    if_f1 = evaluate_f1(labels, scores_to_binary_predictions(if_scores_all, if_threshold))
    ae_f1 = evaluate_f1(labels, scores_to_binary_predictions(recon_errors_all, ae_threshold))

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    if_onnx_path = artifacts_dir / "isolation_forest.onnx"
    ae_onnx_path = artifacts_dir / "autoencoder.onnx"
    calibration_path = artifacts_dir / "health_index_calibration.json"
    manifest_path = artifacts_dir / "manifest.json"

    export_isolation_forest_to_onnx(
        isolation_forest, n_features=feature_matrix.shape[1], path=if_onnx_path
    )
    export_autoencoder_to_onnx(autoencoder, window_length=window_length, path=ae_onnx_path)
    calibration.to_json(calibration_path)

    # JSON manifest (not a Python object) is the contract with `edge`: edge
    # and ml are independent services with no shared package (DD-002), the
    # same reasoning DD-026 already applies to the state_history schema.
    manifest_path.write_text(
        json.dumps(
            {
                "window_length": window_length,
                "feature_order": FEATURE_ORDER,
                "isolation_forest_onnx": if_onnx_path.name,
                "autoencoder_onnx": ae_onnx_path.name,
                "health_index_calibration": calibration_path.name,
                "ood_bounds": {
                    "lower": ood_bounds.lower.tolist(),
                    "upper": ood_bounds.upper.tolist(),
                },
                "isolation_forest_f1": if_f1,
                "autoencoder_f1": ae_f1,
                "used_synthetic_data": used_synthetic,
            },
            indent=2,
        )
    )

    return TrainingSummary(
        used_synthetic_data=used_synthetic,
        n_training_windows=len(windows),
        isolation_forest_f1=if_f1,
        autoencoder_f1=ae_f1,
        manifest_path=manifest_path,
    )


def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS_DIR)
    parser.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="Train on synthetic placeholder data if the real CWRU dataset isn't present "
        "(design.md DD-031) — off by default so a misconfigured data path fails loudly "
        "instead of silently training a placeholder model.",
    )
    args = parser.parse_args()

    summary = run_training_pipeline(
        data_dir=args.data_dir,
        artifacts_dir=args.artifacts_dir,
        allow_synthetic=args.allow_synthetic,
    )
    logger.info("Training complete: %s", summary)


if __name__ == "__main__":
    _main()
