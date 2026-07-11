import random

from edge.providers.base import SensorProvider, SensorSample, VibrationFeatures

_SAMPLING_HZ = 3200


class SimulatedSensorProvider(SensorProvider):
    """Generates plausible vibration/temperature readings for local development."""

    def __init__(self, baseline_temp_c: float = 45.0) -> None:
        self._baseline_temp_c = baseline_temp_c

    def read(self) -> SensorSample:
        rms_g = round(random.uniform(0.05, 0.5), 4)
        crest_factor = round(random.uniform(3.0, 6.0), 3)
        vibration = VibrationFeatures(
            rms_g=rms_g,
            kurtosis=round(random.gauss(3.0, 0.3), 3),
            crest_factor=crest_factor,
            # Peak-to-peak derived from crest_factor/rms (peak ~= crest_factor
            # * rms, peak-to-peak ~= 2x peak for roughly symmetric vibration)
            # so the simulated fields stay internally consistent rather than
            # independently randomized.
            peak_to_peak_g=round(2 * crest_factor * rms_g, 4),
            sampling_hz=_SAMPLING_HZ,
        )
        return SensorSample(
            vibration=vibration,
            temperature_c=round(random.gauss(self._baseline_temp_c, 2.0), 2),
        )
