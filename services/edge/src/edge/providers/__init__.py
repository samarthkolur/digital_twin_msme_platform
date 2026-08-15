from edge.providers.base import SensorProvider, SensorSample

__all__ = ["SensorProvider", "SensorSample", "get_provider"]


def get_provider(name: str) -> SensorProvider:
    if name == "simulated":
        # Lazy import (matching the "hardware" branch below): edge.providers.simulated
        # imports edge.features, which imports edge.providers.base — importing it
        # eagerly here would run this package's __init__ before edge.features has
        # finished initializing, a circular import.
        from edge.providers.simulated import SimulatedSensorProvider

        return SimulatedSensorProvider()
    if name == "hardware":
        from edge.providers.hardware import HardwareSensorProvider

        return HardwareSensorProvider()
    raise ValueError(f"Unknown sensor provider: {name!r}")
