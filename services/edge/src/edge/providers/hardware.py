import struct
import time

from edge.features import compute_vibration_features
from edge.providers.base import SensorProvider, SensorSample

# ADXL345 register map (Analog Devices ADXL345 datasheet, Rev. G).
_REG_DEVID = 0x00
_REG_BW_RATE = 0x2C
_REG_POWER_CTL = 0x2D
_REG_DATA_FORMAT = 0x31
_REG_DATAX0 = 0x32  # DATAX0..DATAZ1 follow contiguously (6 bytes, X/Y/Z, LSB first).

# The ADXL345 reports a fixed device ID. Reading it is the installation smoke
# test: a module whose bus connection is intermittent (an unsoldered breakout
# header is the usual cause) returns a well-formed all-zero identity while its
# supply rails still measure correct, so without this gate that fault
# propagates as plausible data rather than as an error.
_DEVID_ADXL345 = 0xE5

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
# real hardware, tracked as a Pending Task (§24). This burst is enough for a
# first-order feature estimate of the AC-coupled (gravity-removed) vibration.
_SAMPLE_COUNT = 64
_SAMPLING_HZ = 800
_SAMPLE_INTERVAL_S = 1.0 / _SAMPLING_HZ


class HardwareSensorProvider(SensorProvider):
    """Reads the ADXL345 (SPI) and DS18B20 (1-Wire) sensors on a Raspberry Pi."""

    def __init__(self, spi_bus: int = 0, spi_device: int = 0) -> None:
        import spidev
        from w1thermsensor import W1ThermSensor

        self._spi = spidev.SpiDev()
        self._spi.open(spi_bus, spi_device)
        self._spi.max_speed_hz = 5_000_000
        self._spi.mode = 0b11  # ADXL345 SPI requires mode 3 (CPOL=1, CPHA=1).

        self._assert_device_identity()

        self._temp_sensor = W1ThermSensor()

        self._write_register(_REG_DATA_FORMAT, _DATA_FORMAT_FULL_RES | _DATA_FORMAT_RANGE_16G)
        self._write_register(_REG_BW_RATE, _BW_RATE_800HZ)
        self._write_register(_REG_POWER_CTL, _POWER_CTL_MEASURE)

    def _write_register(self, register: int, value: int) -> None:
        self._spi.xfer2([register & ~_READ_BIT, value])

    def _read_register(self, register: int) -> int:
        return int(self._spi.xfer2([register | _READ_BIT, 0])[1])

    def _assert_device_identity(self) -> None:
        """Fails fast unless the ADXL345 reports its documented device ID."""
        devid = self._read_register(_REG_DEVID)
        if devid != _DEVID_ADXL345:
            raise RuntimeError(
                f"ADXL345 identity check failed: DEVID=0x{devid:02X}, "
                f"expected 0x{_DEVID_ADXL345:02X}. "
                + (
                    "An all-zero identity usually means the SPI bus is not "
                    "reaching the part -- check that the breakout header is "
                    "soldered rather than press-fitted, and that MISO/MOSI/"
                    "SCLK/CS are wired to the bus this provider opened."
                    if devid == 0x00
                    else "Check the wiring and that the part is an ADXL345."
                )
            )

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

        vibration = compute_vibration_features(magnitudes_g, _SAMPLING_HZ)

        return SensorSample(
            vibration=vibration,
            temperature_c=round(self._temp_sensor.get_temperature(), 2),
            raw_vibration_window_g=magnitudes_g,
        )

    def close(self) -> None:
        self._spi.close()
