import random

from edge.providers.base import SensorProvider, SensorSample


class SimulatedSensorProvider(SensorProvider):
    """Generates plausible vibration/temperature readings for local development."""

    def __init__(self, baseline_temp_c: float = 45.0) -> None:
        self._baseline_temp_c = baseline_temp_c

    def read(self) -> SensorSample:
        return SensorSample(
            vibration_rms_g=round(random.uniform(0.05, 0.5), 4),
            temperature_c=round(random.gauss(self._baseline_temp_c, 2.0), 2),
        )
