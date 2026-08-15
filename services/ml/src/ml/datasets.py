"""CWRU / IMS Bearing dataset loading (design.md §6.3, §18).

Neither dataset is downloaded into this repo (§24 Pending Tasks: "Download/
preprocess CWRU + IMS datasets into services/ml"). These loaders read from a
configurable directory (default `services/ml/data/`, gitignored) and raise a
clear, actionable error rather than silently falling back to synthetic data
when the real files aren't there — `run_training_pipeline` (pipeline.py)
makes the synthetic-data fallback an explicit, logged opt-in, not a hidden
default, so a real training run can never silently end up training on fake
data because a path was misconfigured.
"""

from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class DatasetNotFoundError(FileNotFoundError):
    pass


def _require_dataset_dir(data_dir: Path, dataset_name: str, source_url: str) -> Path:
    if not data_dir.is_dir() or not any(data_dir.iterdir()):
        raise DatasetNotFoundError(
            f"{dataset_name} dataset not found at {data_dir}. Download it from {source_url} "
            f"and extract into that directory (see design.md §6.3, §24 Pending Tasks), or pass "
            f"allow_synthetic=True to run_training_pipeline (ml.pipeline) to develop/test against "
            f"placeholder data instead."
        )
    return data_dir


def cwru_data_dir(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    return _require_dataset_dir(
        data_dir / "cwru",
        "CWRU Bearing",
        "https://engineering.case.edu/bearingdatacenter",
    )


def ims_data_dir(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    return _require_dataset_dir(
        data_dir / "ims",
        "IMS Bearing",
        "https://data.nasa.gov/dataset/IMS-Bearings",
    )
