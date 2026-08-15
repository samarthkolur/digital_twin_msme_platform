"""1D convolutional autoencoder for raw-window anomaly detection (design.md §6.3 step 2)."""

from pathlib import Path

import numpy as np
import torch
from numpy.typing import NDArray
from torch import nn
from torch.nn import functional as torch_functional


class Conv1DAutoencoder(nn.Module):
    """Three-stage downsample/upsample 1D conv autoencoder. Works on any
    input window length: the decoder's final step interpolates back to the
    exact input length rather than relying on stride/padding arithmetic to
    land exactly on it (real windows come from CWRU/IMS at various lengths;
    synthetic/test windows use shorter lengths for speed), so reconstruction
    error is always computed elementwise against the real input.
    """

    def __init__(self, latent_channels: int = 32) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(1, 8, kernel_size=7, stride=2, padding=3),
            nn.ReLU(),
            nn.Conv1d(8, 16, kernel_size=7, stride=2, padding=3),
            nn.ReLU(),
            nn.Conv1d(16, latent_channels, kernel_size=7, stride=2, padding=3),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="nearest"),
            nn.Conv1d(latent_channels, 16, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.Upsample(scale_factor=2, mode="nearest"),
            nn.Conv1d(16, 8, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.Upsample(scale_factor=2, mode="nearest"),
            nn.Conv1d(8, 1, kernel_size=7, padding=3),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, 1, length) -> reconstruction of the same shape."""
        decoded: torch.Tensor = self.decoder(self.encoder(x))
        if decoded.shape[-1] != x.shape[-1]:
            decoded = torch_functional.interpolate(
                decoded, size=x.shape[-1], mode="linear", align_corners=False
            )
        return decoded


def _to_model_input(windows: NDArray[np.float64]) -> torch.Tensor:
    """(n_windows, length) -> (n_windows, 1, length), each window mean-centred
    the same way `ml.features.compute_window_features` centres it, so the
    autoencoder learns the dynamic (AC-coupled) signal rather than fitting
    the DC offset.
    """
    centred = windows - windows.mean(axis=1, keepdims=True)
    return torch.tensor(centred, dtype=torch.float32).unsqueeze(1)


def train_autoencoder(
    windows: NDArray[np.float64],
    epochs: int = 20,
    learning_rate: float = 1e-3,
    seed: int = 0,
) -> Conv1DAutoencoder:
    """Trains on normal-only windows (reconstruction-error anomaly detection
    assumes the model has only learned to reconstruct healthy vibration,
    design.md §6.3) — callers are responsible for passing normal-class data.
    """
    torch.manual_seed(seed)
    model = Conv1DAutoencoder()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    inputs = _to_model_input(windows)

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        reconstruction = model(inputs)
        loss = torch_functional.mse_loss(reconstruction, inputs)
        loss.backward()  # type: ignore[no-untyped-call]
        optimizer.step()

    model.eval()
    return model


def reconstruction_error(
    model: Conv1DAutoencoder, windows: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Per-window mean squared reconstruction error — the raw signal
    `ml.health_index` and OOD/alert logic threshold against (design.md §6.3).
    """
    model.eval()
    inputs = _to_model_input(windows)
    with torch.no_grad():
        reconstruction = model(inputs)
        error = torch_functional.mse_loss(reconstruction, inputs, reduction="none")
        per_window_error = error.mean(dim=(1, 2))
    return per_window_error.numpy()


def export_autoencoder_to_onnx(model: Conv1DAutoencoder, window_length: int, path: Path) -> None:
    """Exports to ONNX (design.md DD-031). Uses a dynamic batch axis so
    `edge` can run inference one window at a time in production while tests
    can batch many windows through the same exported graph."""
    model.eval()
    dummy_input = torch.zeros(1, 1, window_length, dtype=torch.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        model,
        (dummy_input,),
        str(path),
        input_names=["input"],
        output_names=["reconstruction"],
        dynamic_axes={"input": {0: "batch"}, "reconstruction": {0: "batch"}},
    )
