from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VibrationFeatures:
    """Statistical vibration features (design.md §6.0 state model), computed
    over a short sample window after removing the window's static (gravity)
    offset — see `edge.features.compute_vibration_features`.
    """

    rms_g: float
    kurtosis: float
    crest_factor: float
    peak_to_peak_g: float
    sampling_hz: int


@dataclass(frozen=True, slots=True)
class SensorSample:
    vibration: VibrationFeatures
    temperature_c: float
    # The raw AC-coupled magnitude window `vibration` was computed from
    # (design.md §6.3 DD-031) — kept alongside the derived features so
    # `edge.ml_inference` can feed the autoencoder, which operates on the raw
    # window rather than the four statistical features.
    raw_vibration_window_g: list[float]


class SensorProvider(ABC):
    """Abstract interface for vibration + temperature sensor acquisition.

    Application code depends only on this interface, never on SPI/GPIO/1-Wire
    directly, so the edge service behaves identically against simulated data
    in development and real sensors on the deployed Raspberry Pi.
    """

    @abstractmethod
    def read(self) -> SensorSample: ...

    def close(self) -> None:
        return None
