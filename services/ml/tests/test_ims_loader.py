from pathlib import Path

import numpy as np
import pytest

from ml.ims_loader import load_ims_rul_windows, load_ims_windows


def _write_run(
    run_dir: Path, n_files: int, n_rows: int, n_columns: int, degrading_column: int
) -> None:
    """Writes a synthetic IMS-style run: `n_files` chronologically-named
    ASCII snapshots, each an (n_rows, n_columns) whitespace-delimited text
    file. `degrading_column`'s amplitude grows across the run (simulating a
    degrading bearing); every other column stays flat noise.
    """
    run_dir.mkdir(parents=True)
    rng = np.random.default_rng(0)
    for i in range(n_files):
        # Zero-padded, timestamp-shaped name so lexicographic sort == chronological order.
        filename = f"2004.02.{i:02d}.00.00.00"
        data = rng.normal(scale=0.1, size=(n_rows, n_columns))
        growth_factor = 1.0 + 5.0 * (i / max(n_files - 1, 1))
        data[:, degrading_column] *= growth_factor
        np.savetxt(run_dir / filename, data)


def test_load_ims_windows_labels_early_life_normal_late_life_faulty(tmp_path: Path) -> None:
    ims_dir = tmp_path / "ims"
    _write_run(ims_dir / "1st_test", n_files=40, n_rows=256, n_columns=4, degrading_column=2)

    windows, labels = load_ims_windows(
        ims_dir, window_length=32, files_per_class_per_run=5, windows_per_file=4
    )

    assert windows.shape[1] == 32
    assert set(np.unique(labels).tolist()) == {0, 1}
    assert (labels == 0).sum() > 0
    assert (labels == 1).sum() > 0


def test_most_degrading_column_is_found_automatically(tmp_path: Path) -> None:
    ims_dir = tmp_path / "ims"
    # Column 3 is the one that grows — the loader must find it without being
    # told, since real IMS mirrors vary in column order (design.md DD-039).
    _write_run(ims_dir / "2nd_test", n_files=30, n_rows=256, n_columns=4, degrading_column=3)

    from ml.ims_loader import _list_snapshot_files, _most_degrading_column

    files = _list_snapshot_files(ims_dir / "2nd_test")
    assert _most_degrading_column(files, sample_size=10) == 3


def test_load_ims_windows_pools_multiple_test_runs(tmp_path: Path) -> None:
    ims_dir = tmp_path / "ims"
    _write_run(ims_dir / "1st_test", n_files=30, n_rows=256, n_columns=8, degrading_column=4)
    _write_run(ims_dir / "2nd_test", n_files=30, n_rows=256, n_columns=4, degrading_column=0)

    windows, labels = load_ims_windows(
        ims_dir, window_length=32, files_per_class_per_run=5, windows_per_file=4
    )

    # Both runs should contribute windows to both classes.
    assert (labels == 0).sum() >= 2 * 5 * 4 * 0.5
    assert (labels == 1).sum() >= 2 * 5 * 4 * 0.5


def test_load_ims_windows_raises_when_no_run_directories(tmp_path: Path) -> None:
    ims_dir = tmp_path / "ims"
    ims_dir.mkdir()
    (ims_dir / "readme.txt").write_text("not a run directory")

    with pytest.raises(ValueError, match="No IMS test-run directories"):
        load_ims_windows(ims_dir, window_length=32)


def test_load_ims_windows_finds_nested_run_directories(tmp_path: Path) -> None:
    # Some IMS mirrors wrap the test-run folders in an extra top-level
    # directory (e.g. "4. Bearings/1st_test/...") — the loader must still
    # find them via a recursive search, not just the top level.
    ims_dir = tmp_path / "ims"
    _write_run(
        ims_dir / "4. Bearings" / "1st_test",
        n_files=30,
        n_rows=256,
        n_columns=4,
        degrading_column=1,
    )

    windows, labels = load_ims_windows(
        ims_dir, window_length=32, files_per_class_per_run=5, windows_per_file=4
    )
    assert len(windows) > 0


def test_load_ims_rul_windows_targets_span_full_life_range(tmp_path: Path) -> None:
    ims_dir = tmp_path / "ims"
    _write_run(ims_dir / "1st_test", n_files=40, n_rows=256, n_columns=4, degrading_column=2)

    windows_train, targets_train, windows_test, targets_test = load_ims_rul_windows(
        ims_dir, window_length=32, files_per_run=20, windows_per_file=3, test_fraction=0.2
    )

    assert windows_train.shape[1] == 32
    assert len(windows_train) == len(targets_train) > 0
    assert len(windows_test) == len(targets_test) > 0
    all_targets = np.concatenate([targets_train, targets_test])
    # Targets are a 0..1 life-fraction-remaining, not the binary 0/1 labels
    # load_ims_windows uses — there should be values spread across the range,
    # not just two extremes.
    assert all_targets.min() >= 0.0
    assert all_targets.max() <= 1.0
    assert len(np.unique(all_targets)) > 2


def test_load_ims_rul_windows_splits_by_file_not_by_window(tmp_path: Path) -> None:
    ims_dir = tmp_path / "ims"
    _write_run(ims_dir / "1st_test", n_files=30, n_rows=256, n_columns=4, degrading_column=1)

    windows_train, targets_train, windows_test, targets_test = load_ims_rul_windows(
        ims_dir, window_length=32, files_per_run=30, windows_per_file=5, test_fraction=0.3, seed=1
    )

    # Every window from one source file shares that file's exact target
    # value, so if train/test were split correctly by file (not leaking
    # windows from the same file into both), the set of train targets and
    # the set of test targets should be disjoint.
    assert set(np.unique(targets_train).tolist()).isdisjoint(set(np.unique(targets_test).tolist()))


def test_load_ims_rul_windows_raises_when_no_run_directories(tmp_path: Path) -> None:
    ims_dir = tmp_path / "ims"
    ims_dir.mkdir()

    with pytest.raises(ValueError, match="No IMS test-run directories"):
        load_ims_rul_windows(ims_dir, window_length=32)
