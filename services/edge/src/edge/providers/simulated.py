import random

from edge.features import compute_vibration_features
from edge.providers.base import SensorProvider, SensorSample

# Matches services/ml/src/ml/pipeline.py's DEFAULT_WINDOW_LENGTH, which in
# turn matches hardware.py's real _SAMPLE_COUNT (DD-022) — the simulated
# provider's raw window needs to be the same length real hardware produces
# so `edge.ml_inference` behaves identically against either provider.
_SAMPLE_COUNT = 64
_SAMPLING_HZ = 3200
_DC_OFFSET_G = 1.0


class SimulatedSensorProvider(SensorProvider):
    """Generates plausible vibration/temperature readings for local development.

    Generates a raw magnitude window first and derives the four statistical
    features from it via the same `compute_vibration_features` the hardware
    provider uses, rather than randomizing the features independently — this
    keeps the four fields internally consistent (design.md §6.0) and gives
    `edge.ml_inference` a real raw window to run the autoencoder against.
    """

    def __init__(self, baseline_temp_c: float = 45.0) -> None:
        self._baseline_temp_c = baseline_temp_c

    def read(self) -> SensorSample:
        magnitudes_g = [random.gauss(_DC_OFFSET_G, 0.08) for _ in range(_SAMPLE_COUNT)]
        vibration = compute_vibration_features(magnitudes_g, _SAMPLING_HZ)

        return SensorSample(
            vibration=vibration,
            temperature_c=round(random.gauss(self._baseline_temp_c, 2.0), 2),
            raw_vibration_window_g=magnitudes_g,
        )
