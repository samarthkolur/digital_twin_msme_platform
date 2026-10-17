from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

from ml.cwru_loader import load_cwru_windows


def _write_fixture_mat(path: Path, variable_name: str, n_samples: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    sio.savemat(path, {variable_name: rng.normal(size=(n_samples, 1))})


def test_load_cwru_windows_reads_normal_and_faulty_files(tmp_path: Path) -> None:
    cwru_dir = tmp_path / "cwru"
    cwru_dir.mkdir()
    # Variable names embed CWRU's own numeric file IDs, not this repo's
    # descriptive filenames — matching the real dataset's actual layout.
    _write_fixture_mat(cwru_dir / "Normal_0.mat", "X097_DE_time", n_samples=64 * 20, seed=1)
    _write_fixture_mat(cwru_dir / "IR007_0.mat", "X105_DE_time", n_samples=64 * 20, seed=2)

    windows, labels = load_cwru_windows(cwru_dir, window_length=64, max_windows_per_faulty_file=5)

    assert windows.shape[1] == 64
    assert set(np.unique(labels).tolist()) == {0, 1}
    assert (labels == 0).sum() > 0
    assert (labels == 1).sum() == 5


def test_load_cwru_windows_balances_normal_files_against_more_numerous_faulty_files(
    tmp_path: Path,
) -> None:
    cwru_dir = tmp_path / "cwru"
    cwru_dir.mkdir()
    _write_fixture_mat(cwru_dir / "Normal_0.mat", "X097_DE_time", n_samples=64 * 1000, seed=1)
    for label, var in [("IR007_0", "X105_DE_time"), ("B007_0", "X118_DE_time")]:
        _write_fixture_mat(cwru_dir / f"{label}.mat", var, n_samples=64 * 1000, seed=3)

    windows, labels = load_cwru_windows(cwru_dir, window_length=64, max_windows_per_faulty_file=10)

    # 1 normal file, 2 faulty files, cap=10 -> normal file's cap should scale
    # to 10 * 2/1 = 20 windows, not also be capped at 10 (design.md §24).
    assert (labels == 0).sum() == 20
    assert (labels == 1).sum() == 20


def test_load_cwru_windows_skips_uncatalogued_files(tmp_path: Path) -> None:
    cwru_dir = tmp_path / "cwru"
    cwru_dir.mkdir()
    _write_fixture_mat(cwru_dir / "Normal_0.mat", "X097_DE_time", n_samples=64 * 20, seed=1)
    _write_fixture_mat(cwru_dir / "not_a_real_label.mat", "X999_DE_time", n_samples=64 * 20, seed=4)

    windows, labels = load_cwru_windows(cwru_dir, window_length=64, max_windows_per_faulty_file=5)

    assert len(windows) == len(labels) > 0
    assert (labels == 1).sum() == 0  # the uncatalogued file was never counted as faulty


def test_load_cwru_windows_raises_when_no_recognized_files(tmp_path: Path) -> None:
    cwru_dir = tmp_path / "cwru"
    cwru_dir.mkdir()
    _write_fixture_mat(cwru_dir / "unknown.mat", "X999_DE_time", n_samples=64, seed=1)

    with pytest.raises(ValueError, match="No recognized CWRU"):
        load_cwru_windows(cwru_dir, window_length=64)


def test_load_cwru_windows_raises_on_missing_drive_end_channel(tmp_path: Path) -> None:
    cwru_dir = tmp_path / "cwru"
    cwru_dir.mkdir()
    sio.savemat(cwru_dir / "Normal_0.mat", {"X097_FE_time": np.zeros((640, 1))})

    with pytest.raises(ValueError, match="DE_time"):
        load_cwru_windows(cwru_dir, window_length=64)
