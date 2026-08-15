from pathlib import Path

import pytest

from ml.datasets import DatasetNotFoundError, cwru_data_dir, ims_data_dir


def test_cwru_data_dir_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(DatasetNotFoundError, match="CWRU"):
        cwru_data_dir(tmp_path)


def test_ims_data_dir_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(DatasetNotFoundError, match="IMS"):
        ims_data_dir(tmp_path)


def test_cwru_data_dir_raises_when_directory_exists_but_is_empty(tmp_path: Path) -> None:
    (tmp_path / "cwru").mkdir()

    with pytest.raises(DatasetNotFoundError):
        cwru_data_dir(tmp_path)


def test_cwru_data_dir_returns_path_when_populated(tmp_path: Path) -> None:
    cwru_dir = tmp_path / "cwru"
    cwru_dir.mkdir()
    (cwru_dir / "normal_0.mat").write_bytes(b"placeholder")

    assert cwru_data_dir(tmp_path) == cwru_dir
