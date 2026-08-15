from pathlib import Path

import numpy as np
import torch

from ml.autoencoder import (
    Conv1DAutoencoder,
    export_autoencoder_to_onnx,
    reconstruction_error,
    train_autoencoder,
)


def _normal_windows(n: int, length: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 1.0 + rng.normal(loc=0.0, scale=0.05, size=(n, length))


def test_forward_pass_preserves_input_length_for_arbitrary_lengths() -> None:
    for length in (17, 32, 64, 101):
        model = Conv1DAutoencoder()
        x = torch.zeros(2, 1, length)
        output = model(x)
        assert output.shape == (2, 1, length)


def test_reconstruction_error_is_lower_for_normal_than_faulty_after_training() -> None:
    normal = _normal_windows(40, length=64)
    model = train_autoencoder(normal, epochs=15, seed=0)

    faulty = normal.copy()
    faulty[:, 30] += 3.0  # inject an out-of-distribution spike

    normal_error = reconstruction_error(model, normal).mean()
    faulty_error = reconstruction_error(model, faulty).mean()

    assert faulty_error > normal_error


def test_export_autoencoder_to_onnx_writes_a_file(tmp_path: Path) -> None:
    normal = _normal_windows(10, length=32)
    model = train_autoencoder(normal, epochs=2, seed=0)

    output_path = tmp_path / "autoencoder.onnx"
    export_autoencoder_to_onnx(model, window_length=32, path=output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0
