from edge.providers.base import SensorProvider, SensorSample


class HardwareSensorProvider(SensorProvider):
    """Reads the ADXL345 (SPI) and DS18B20 (1-Wire) sensors on a Raspberry Pi.

    Hardware libraries are imported lazily so this module can be loaded on
    non-Pi hosts (CI, dev containers) without the optional `hardware`
    dependency group installed. Register decoding lands in Phase 2 (IoT data
    pipeline); this is the provider-selection skeleton only.
    """

    def __init__(self, spi_bus: int = 0, spi_device: int = 0) -> None:
        import spidev
        from w1thermsensor import W1ThermSensor

        self._spi = spidev.SpiDev()
        self._spi.open(spi_bus, spi_device)
        self._spi.max_speed_hz = 5_000_000
        self._temp_sensor = W1ThermSensor()

    def read(self) -> SensorSample:
        raise NotImplementedError(
            "ADXL345 register decoding is implemented in Phase 2 (IoT data pipeline)."
        )

    def close(self) -> None:
        self._spi.close()
