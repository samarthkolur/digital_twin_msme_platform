import struct
import time
from statistics import fmean

from edge.providers.base import SensorProvider, SensorSample

# ADXL345 register map (Analog Devices ADXL345 datasheet, Rev. G).
_REG_BW_RATE = 0x2C
_REG_POWER_CTL = 0x2D
_REG_DATA_FORMAT = 0x31
_REG_DATAX0 = 0x32  # DATAX0..DATAZ1 follow contiguously (6 bytes, X/Y/Z, LSB first).

_READ_BIT = 0x80
_MULTI_BYTE_BIT = 0x40

_POWER_CTL_MEASURE = 0x08
_DATA_FORMAT_FULL_RES = 0x08
_DATA_FORMAT_RANGE_16G = 0x03
_BW_RATE_800HZ = 0x0D

# Fixed 3.9 mg/LSB scale factor in full-resolution mode, independent of the
# selected g-range (datasheet §Register 0x31).
_SCALE_G_PER_LSB = 0.0039

# Samples per `read()` call. A short burst rather than a continuous 3,200 Hz
# stream: bit-banging that rate reliably from Python inside an async event
# loop is a real-time-systems problem (buffering, jitter) best tuned against
# real hardware, tracked as Phase 3 work. This burst is enough for a
# first-order RMS estimate of the AC-coupled (gravity-removed) vibration.
_SAMPLE_COUNT = 64
_SAMPLE_INTERVAL_S = 1.0 / 800


class HardwareSensorProvider(SensorProvider):
    """Reads the ADXL345 (SPI) and DS18B20 (1-Wire) sensors on a Raspberry Pi."""

    def __init__(self, spi_bus: int = 0, spi_device: int = 0) -> None:
        import spidev
        from w1thermsensor import W1ThermSensor

        self._spi = spidev.SpiDev()
        self._spi.open(spi_bus, spi_device)
        self._spi.max_speed_hz = 5_000_000
        self._spi.mode = 0b11  # ADXL345 SPI requires mode 3 (CPOL=1, CPHA=1).
        self._temp_sensor = W1ThermSensor()

        self._write_register(_REG_DATA_FORMAT, _DATA_FORMAT_FULL_RES | _DATA_FORMAT_RANGE_16G)
        self._write_register(_REG_BW_RATE, _BW_RATE_800HZ)
        self._write_register(_REG_POWER_CTL, _POWER_CTL_MEASURE)

    def _write_register(self, register: int, value: int) -> None:
        self._spi.xfer2([register & ~_READ_BIT, value])

    def _read_axes_raw(self) -> tuple[int, int, int]:
        """Reads one X/Y/Z sample as signed 16-bit LSB-first register values."""
        response = self._spi.xfer2([_REG_DATAX0 | _READ_BIT | _MULTI_BYTE_BIT, *([0] * 6)])
        x, y, z = struct.unpack("<hhh", bytes(response[1:7]))
        return x, y, z

    def read(self) -> SensorSample:
        magnitudes_g = []
        for _ in range(_SAMPLE_COUNT):
            x, y, z = self._read_axes_raw()
            x_g, y_g, z_g = (v * _SCALE_G_PER_LSB for v in (x, y, z))
            magnitudes_g.append((x_g**2 + y_g**2 + z_g**2) ** 0.5)
            time.sleep(_SAMPLE_INTERVAL_S)

        # RMS of the AC-coupled signal: subtract the window mean (which is
        # dominated by the ~1g gravity component at this mount orientation)
        # before computing RMS, so the result reflects dynamic vibration
        # rather than the static offset.
        mean_g = fmean(magnitudes_g)
        vibration_rms_g = fmean((m - mean_g) ** 2 for m in magnitudes_g) ** 0.5

        return SensorSample(
            vibration_rms_g=round(vibration_rms_g, 4),
            temperature_c=round(self._temp_sensor.get_temperature(), 2),
        )

    def close(self) -> None:
        self._spi.close()
