from edge.providers.base import SensorProvider, SensorSample
from edge.providers.simulated import SimulatedSensorProvider

__all__ = ["SensorProvider", "SensorSample", "get_provider"]


def get_provider(name: str) -> SensorProvider:
    if name == "simulated":
        return SimulatedSensorProvider()
    if name == "hardware":
        from edge.providers.hardware import HardwareSensorProvider

        return HardwareSensorProvider()
    raise ValueError(f"Unknown sensor provider: {name!r}")
