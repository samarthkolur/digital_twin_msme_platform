"""Loads the real, downloaded CWRU Bearing dataset into (windows, labels)
arrays (design.md §6.3, §24 Pending Tasks — this closes the "Download/
preprocess CWRU + IMS datasets" item's CWRU half).

Reads every `<label>.mat` file in the directory `ml.datasets.cwru_data_dir()`
resolves (populated by `scripts/download_data.py`), matches each file's
`<label>` stem against `ml.cwru_metadata.CWRU_FILE_INFO` to get its ground-
truth condition, extracts the Drive-End accelerometer channel, and segments
it into fixed-length windows exactly like `ml.synthetic.generate_labeled_dataset`
does for the placeholder path — same (windows, labels) contract, real data.

Sampling-rate caveat (see design.md DD-039): CWRU's Drive-End channel is
sampled at 12 kHz; `services/edge`'s real ADXL345 burst (DD-022) samples at
800 Hz. Both are windowed to the same *sample count* (`window_length`, not
duration) for ONNX input-shape compatibility, so a training window here
spans a different, shorter physical duration than a real edge window at the
same `window_length`. The four statistical features this pipeline actually
trains on (RMS/kurtosis/crest factor/peak-to-peak) are amplitude/shape
statistics, not timescale-dependent, but this cross-sampling-rate assumption
has not been empirically validated against real edge hardware — tracked
honestly as an open item (§25), not silently assumed correct.
"""

from pathlib import Path

import numpy as np
import scipy.io as sio
from numpy.typing import NDArray

from ml.cwru_metadata import CWRU_FILE_INFO

# Each CWRU recording has ~120k-480k samples; capping windows per file bounds
# total dataset size (and autoencoder training time) without needing every
# possible window from every file to get a representative, real dataset.
DEFAULT_MAX_WINDOWS_PER_FAULTY_FILE = 300


def _load_drive_end_channel(mat_path: Path) -> NDArray[np.float64]:
    """CWRU .mat variable names embed the site's internal numeric file ID
    (e.g. "X097_DE_time"), not this repo's descriptive `<label>.mat`
    filename — so the Drive-End channel is found by suffix match, not by
    reconstructing the original file number.
    """
    mat_contents = sio.loadmat(mat_path)
    de_keys = [key for key in mat_contents if key.endswith("_DE_time")]
    if not de_keys:
        raise ValueError(f"{mat_path} has no *_DE_time variable (expected a CWRU Drive-End file)")
    return np.asarray(mat_contents[de_keys[0]], dtype=np.float64).reshape(-1)


def _segment_into_windows(
    signal: NDArray[np.float64], window_length: int, max_windows: int
) -> NDArray[np.float64]:
    n_windows = min(len(signal) // window_length, max_windows)
    trimmed = signal[: n_windows * window_length]
    return trimmed.reshape(n_windows, window_length)


def load_cwru_windows(
    cwru_dir: Path,
    window_length: int,
    max_windows_per_faulty_file: int = DEFAULT_MAX_WINDOWS_PER_FAULTY_FILE,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Returns (windows, labels) over every recognized `.mat` file in
    `cwru_dir` — labels are 0=normal / 1=faulty (inner race, ball, or outer
    race — design.md §6.0's alert model doesn't yet distinguish fault type,
    only anomalous vs. normal), matching `ml.synthetic`'s convention so
    `ml.pipeline` can consume either source identically.

    The standard CWRU catalog (`ml.cwru_metadata`) has far more faulty files
    (60) than normal ones (4), so normal files get a proportionally higher
    per-file window cap (`max_windows_per_faulty_file * n_faulty / n_normal`)
    rather than the same cap — otherwise the resulting dataset would be
    ~94% faulty windows, which is backwards from both a realistic class
    balance and a useful held-out F1 evaluation set (design.md §9).
    """
    catalogued_files = [
        (mat_path, info)
        for mat_path in sorted(cwru_dir.glob("*.mat"))
        for info in [CWRU_FILE_INFO.get(mat_path.stem)]
        if info is not None
    ]
    if not catalogued_files:
        raise ValueError(
            f"No recognized CWRU .mat files found in {cwru_dir} (expected filenames matching "
            f"ml.cwru_metadata.CWRU_FILE_INFO's labels, e.g. 'Normal_0.mat', 'IR007_1.mat')"
        )

    n_normal_files = sum(1 for _, info in catalogued_files if info.fault_type == "normal")
    n_faulty_files = len(catalogued_files) - n_normal_files
    max_windows_per_normal_file = (
        round(max_windows_per_faulty_file * max(n_faulty_files, 1) / n_normal_files)
        if n_normal_files > 0
        else max_windows_per_faulty_file
    )

    all_windows: list[NDArray[np.float64]] = []
    all_labels: list[NDArray[np.int64]] = []
    for mat_path, info in catalogued_files:
        is_normal = info.fault_type == "normal"
        cap = max_windows_per_normal_file if is_normal else max_windows_per_faulty_file
        signal = _load_drive_end_channel(mat_path)
        windows = _segment_into_windows(signal, window_length, cap)
        all_windows.append(windows)
        all_labels.append(np.full(len(windows), 0 if is_normal else 1, dtype=np.int64))

    return np.concatenate(all_windows, axis=0), np.concatenate(all_labels, axis=0)
