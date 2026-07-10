from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SensorSample:
    vibration_rms_g: float
    temperature_c: float


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
