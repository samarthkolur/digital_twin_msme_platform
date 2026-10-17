from pathlib import Path

from edge.phase2 import Phase2Inference


class _Loader:
    def __init__(self) -> None:
        self.calls = 0
        self.engine = object()

    def __call__(self, artifacts_dir: Path) -> object:
        self.calls += 1
        return self.engine


def test_disabled_never_loads_models(tmp_path: Path) -> None:
    loader = _Loader()
    gate = Phase2Inference(tmp_path, loader)  # type: ignore[arg-type]
    assert gate.engine(False) is None
    assert gate.engine(False) is None
    assert loader.calls == 0


def test_enabled_loads_once_and_reloads_after_toggle(tmp_path: Path) -> None:
    loader = _Loader()
    gate = Phase2Inference(tmp_path, loader)  # type: ignore[arg-type]
    assert gate.engine(True) is loader.engine
    assert gate.engine(True) is loader.engine
    assert loader.calls == 1
    assert gate.engine(False) is None
    gate.engine(True)
    assert loader.calls == 2


def test_missing_artifacts_are_not_retried_every_cycle(tmp_path: Path) -> None:
    calls = 0

    def loader(artifacts_dir: Path) -> None:
        nonlocal calls
        calls += 1

    gate = Phase2Inference(tmp_path, loader)
    assert gate.engine(True) is None
    assert gate.engine(True) is None
    assert calls == 1
