"""Loads the real, downloaded IMS Bearing run-to-failure dataset into
(windows, labels) arrays (design.md §6.3, §24 Pending Tasks, DD-039).

Unlike CWRU (discrete, individually labeled fault recordings), IMS is a
*run-to-failure* dataset: three long test runs, each a directory of
chronologically-named ASCII vibration snapshots (one short recording every
few minutes) with no per-snapshot ground-truth label — a bearing degrades
gradually over the run and eventually fails, but the dataset itself doesn't
mark the exact moment "normal" ends and "faulty" begins.

This loader turns that into a binary-labeled dataset with an explicit,
documented heuristic (design.md DD-039): for each test run, it (1) finds the
channel with the largest RMS growth from the run's start to its end — the
degrading bearing/axis, found empirically rather than hardcoded from
documentation, since IMS mirrors vary in column order/count — then (2) labels
snapshots from the *early* portion of the run "normal" and snapshots from the
*late* portion "faulty", skipping the ambiguous middle. This is a reasonable,
literature-consistent proxy label (early-life vs. late-life), not a verified
fault diagnosis at any single point in time — see DD-039 for why, and don't
treat per-window labels here as more precise than that.
"""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

# Bounds total files read (and therefore runtime/memory) — each test run has
# thousands of snapshot files; we don't need all of them for a representative
# labeled dataset.
DEFAULT_FILES_PER_CLASS_PER_RUN = 15
DEFAULT_WINDOWS_PER_FILE = 50
DEFAULT_TREND_SAMPLE_FILES = 20
# Fraction of a run's chronologically-sorted files treated as "early life"
# (label 0) vs. "late life" (label 1); the middle is skipped as an
# unlabelable transition period (design.md DD-039).
EARLY_LIFE_FRACTION = 0.3
LATE_LIFE_FRACTION = 0.1

# RUL regression sampling (design.md DD-040) — spans each run's *entire*
# timeline, not just the early/late extremes above, since a regression
# target needs coverage of the whole degradation curve to be meaningful.
DEFAULT_FILES_PER_RUL_RUN = 60
DEFAULT_RUL_WINDOWS_PER_FILE = 10
DEFAULT_RUL_TEST_FRACTION = 0.2


def _find_run_directories(ims_dir: Path) -> list[Path]:
    """IMS mirrors differ in exact folder naming/nesting (e.g. a wrapping
    "4. Bearings/" directory, "3rd_test" vs "4th_test"); matching any
    directory with "test" in its name, at any depth, is robust to that
    instead of assuming one specific layout.
    """
    return sorted(d for d in ims_dir.rglob("*") if d.is_dir() and "test" in d.name.lower())


def _list_snapshot_files(run_dir: Path) -> list[Path]:
    # Snapshot filenames are zero-padded timestamps (e.g. "2003.10.22.12.06.24"),
    # so lexicographic sort is chronological order.
    return sorted(p for p in run_dir.iterdir() if p.is_file())


def _read_snapshot(path: Path) -> NDArray[np.float64]:
    """Returns (n_rows, n_columns) — `np.loadtxt` collapses single-column
    files to a 1D array, so that case is reshaped back to 2D explicitly.
    """
    data = np.loadtxt(path, dtype=np.float64)
    return data.reshape(-1, 1) if data.ndim == 1 else data


def _most_degrading_column(files: list[Path], sample_size: int) -> int:
    """Reads a small, evenly-spaced sample of a run's files and returns the
    index of the column whose RMS grew the most from the first half of the
    sample to the second half — the channel most consistent with a
    progressively degrading bearing (design.md DD-039).
    """
    sample_indices = np.linspace(0, len(files) - 1, num=min(sample_size, len(files)), dtype=int)
    sampled_rms = [np.sqrt(np.mean(_read_snapshot(files[i]) ** 2, axis=0)) for i in sample_indices]
    rms_over_time = np.stack(sampled_rms)  # (n_samples, n_columns)

    half = len(rms_over_time) // 2
    early_mean = rms_over_time[:half].mean(axis=0)
    late_mean = rms_over_time[half:].mean(axis=0)
    growth = late_mean - early_mean
    return int(np.argmax(growth))


def _windows_from_files(
    files: list[Path], column: int, window_length: int, windows_per_file: int
) -> NDArray[np.float64]:
    windows = []
    for path in files:
        signal = _read_snapshot(path)[:, column]
        n_windows = min(len(signal) // window_length, windows_per_file)
        trimmed = signal[: n_windows * window_length]
        if n_windows > 0:
            windows.append(trimmed.reshape(n_windows, window_length))
    if not windows:
        return np.empty((0, window_length), dtype=np.float64)
    return np.concatenate(windows, axis=0)


def load_ims_windows(
    ims_dir: Path,
    window_length: int,
    files_per_class_per_run: int = DEFAULT_FILES_PER_CLASS_PER_RUN,
    windows_per_file: int = DEFAULT_WINDOWS_PER_FILE,
    trend_sample_files: int = DEFAULT_TREND_SAMPLE_FILES,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Returns (windows, labels) — 0=normal (early-life), 1=faulty
    (late-life) — pooled across every run-to-failure test directory found
    under `ims_dir`, matching `ml.synthetic`'s labeling convention so
    `ml.pipeline` can consume either source identically.
    """
    run_dirs = _find_run_directories(ims_dir)
    if not run_dirs:
        raise ValueError(
            f"No IMS test-run directories found under {ims_dir} (expected subdirectories with "
            f"'test' in their name, e.g. '1st_test', populated by scripts/download_data.py)"
        )

    all_windows: list[NDArray[np.float64]] = []
    all_labels: list[NDArray[np.int64]] = []

    for run_dir in run_dirs:
        files = _list_snapshot_files(run_dir)
        if len(files) < 4:
            continue  # not enough snapshots in this run to form a meaningful early/late split

        column = _most_degrading_column(files, trend_sample_files)

        n_early = max(1, int(len(files) * EARLY_LIFE_FRACTION))
        n_late = max(1, int(len(files) * LATE_LIFE_FRACTION))
        early_files = files[:n_early]
        late_files = files[-n_late:]

        def _sample(candidates: list[Path]) -> list[Path]:
            count = min(files_per_class_per_run, len(candidates))
            indices = np.linspace(0, len(candidates) - 1, num=count, dtype=int)
            return [candidates[i] for i in indices]

        normal_windows = _windows_from_files(
            _sample(early_files), column, window_length, windows_per_file
        )
        faulty_windows = _windows_from_files(
            _sample(late_files), column, window_length, windows_per_file
        )

        all_windows.extend([normal_windows, faulty_windows])
        all_labels.extend(
            [
                np.zeros(len(normal_windows), dtype=np.int64),
                np.ones(len(faulty_windows), dtype=np.int64),
            ]
        )

    if not all_windows or sum(len(w) for w in all_windows) == 0:
        raise ValueError(f"Found IMS test-run directories under {ims_dir} but extracted no windows")

    return np.concatenate(all_windows, axis=0), np.concatenate(all_labels, axis=0)


def load_ims_rul_windows(
    ims_dir: Path,
    window_length: int,
    files_per_run: int = DEFAULT_FILES_PER_RUL_RUN,
    windows_per_file: int = DEFAULT_RUL_WINDOWS_PER_FILE,
    trend_sample_files: int = DEFAULT_TREND_SAMPLE_FILES,
    test_fraction: float = DEFAULT_RUL_TEST_FRACTION,
    seed: int = 0,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Returns (windows_train, targets_train, windows_test, targets_test) for
    remaining-useful-life regression (design.md §6.3, DD-040).

    Unlike `load_ims_windows`'s early/late-only binary labels, this samples
    evenly across a run's *entire* chronologically-sorted file list and
    assigns each sampled file a continuous target: `1.0 - file_index /
    (n_files - 1)` — 1.0 at the run's first file (full life remaining), 0.0
    at its last (failure). This is a life-*position* proxy, not a measured
    time-to-failure in physical units — a run lasting 5 hours and one lasting
    5 days get the same 0.0..1.0 label shape (DD-040).

    The train/test split happens by *file*, not by window: windows drawn from
    the same snapshot file are highly correlated (same few seconds of the
    same run), so splitting at the window level would leak — a model could
    partly "memorize" a file's characteristics from windows seen in training
    and be evaluated on other windows from that same file, inflating held-out
    metrics. Splitting whole files avoids that.
    """
    run_dirs = _find_run_directories(ims_dir)
    if not run_dirs:
        raise ValueError(
            f"No IMS test-run directories found under {ims_dir} (expected subdirectories with "
            f"'test' in their name, e.g. '1st_test', populated by scripts/download_data.py)"
        )

    rng = np.random.default_rng(seed)
    train_windows: list[NDArray[np.float64]] = []
    train_targets: list[NDArray[np.float64]] = []
    test_windows: list[NDArray[np.float64]] = []
    test_targets: list[NDArray[np.float64]] = []

    for run_dir in run_dirs:
        files = _list_snapshot_files(run_dir)
        n_files = len(files)
        if n_files < 4:
            continue

        column = _most_degrading_column(files, trend_sample_files)

        sample_count = min(files_per_run, n_files)
        sampled_indices = np.linspace(0, n_files - 1, num=sample_count, dtype=int)

        is_test = rng.random(sample_count) < test_fraction
        for is_test_file, file_index in zip(is_test, sampled_indices, strict=True):
            life_fraction_remaining = 1.0 - file_index / (n_files - 1)
            windows = _windows_from_files(
                [files[file_index]], column, window_length, windows_per_file
            )
            if len(windows) == 0:
                continue
            targets = np.full(len(windows), life_fraction_remaining, dtype=np.float64)
            if is_test_file:
                test_windows.append(windows)
                test_targets.append(targets)
            else:
                train_windows.append(windows)
                train_targets.append(targets)

    if not train_windows or not test_windows:
        raise ValueError(
            f"Found IMS test-run directories under {ims_dir} but couldn't build a non-empty "
            f"train/test split for RUL regression"
        )

    return (
        np.concatenate(train_windows, axis=0),
        np.concatenate(train_targets, axis=0),
        np.concatenate(test_windows, axis=0),
        np.concatenate(test_targets, axis=0),
    )
