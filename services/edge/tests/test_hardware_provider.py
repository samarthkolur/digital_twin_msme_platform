import struct
import sys
import types
from collections.abc import Iterator

import pytest


class _FakeSpiDev:
    """Stands in for `spidev.SpiDev`, recording register writes and replaying
    a fixed, alternating pair of raw X/Y/Z samples for every register-read
    burst so the resulting RMS is a hand-computable, non-trivial value.
    """

    _SAMPLE_A = (0, 0, 256)  # 256 * 0.0039 g/LSB = 0.9984 g
    _SAMPLE_B = (0, 0, 266)  # 266 * 0.0039 g/LSB = 1.0374 g

    def __init__(self) -> None:
        self.writes: list[tuple[int, int]] = []
        self._read_count = 0
        self.max_speed_hz: int = 0
        self.mode: int = 0

    def open(self, bus: int, device: int) -> None:
        self.bus = bus
        self.device = device

    def xfer2(self, data: list[int]) -> list[int]:
        if len(data) == 2:
            self.writes.append((data[0], data[1]))
            return [0, 0]

        sample = self._SAMPLE_A if self._read_count % 2 == 0 else self._SAMPLE_B
        self._read_count += 1
        return [0, *struct.pack("<hhh", *sample)]

    def close(self) -> None:
        pass


class _FakeW1ThermSensor:
    def get_temperature(self) -> float:
        return 42.5


@pytest.fixture
def fake_hardware_modules() -> Iterator[_FakeSpiDev]:
    """Injects fake `spidev`/`w1thermsensor` modules so `HardwareSensorProvider`
    can be instantiated without the real (Pi-only) `hardware` extra installed.
    """
    fake_spi_instance = _FakeSpiDev()

    fake_spidev = types.ModuleType("spidev")
    fake_spidev.SpiDev = lambda: fake_spi_instance  # type: ignore[attr-defined]

    fake_w1 = types.ModuleType("w1thermsensor")
    fake_w1.W1ThermSensor = _FakeW1ThermSensor  # type: ignore[attr-defined]

    sys.modules["spidev"] = fake_spidev
    sys.modules["w1thermsensor"] = fake_w1
    try:
        yield fake_spi_instance
    finally:
        del sys.modules["spidev"]
        del sys.modules["w1thermsensor"]


def test_init_configures_adxl345_registers(fake_hardware_modules: _FakeSpiDev) -> None:
    from edge.providers.hardware import HardwareSensorProvider

    HardwareSensorProvider()

    assert fake_hardware_modules.max_speed_hz == 5_000_000
    assert fake_hardware_modules.mode == 0b11
    assert fake_hardware_modules.writes == [
        (0x31, 0x08 | 0x03),  # DATA_FORMAT: full-res | +-16g range
        (0x2C, 0x0D),  # BW_RATE: 800 Hz
        (0x2D, 0x08),  # POWER_CTL: measurement mode
    ]


def test_read_computes_ac_coupled_rms_and_temperature(
    fake_hardware_modules: _FakeSpiDev,
) -> None:
    from edge.providers.hardware import HardwareSensorProvider

    provider = HardwareSensorProvider()
    sample = provider.read()

    # mean magnitude = (0.9984 + 1.0374) / 2 = 1.0179; each sample deviates
    # from it by exactly +-0.0195 g, so RMS of the AC-coupled signal is 0.0195.
    assert sample.vibration_rms_g == pytest.approx(0.0195, abs=1e-4)
    assert sample.temperature_c == 42.5


def test_close_closes_spi(fake_hardware_modules: _FakeSpiDev) -> None:
    from edge.providers.hardware import HardwareSensorProvider

    provider = HardwareSensorProvider()
    closed = []
    fake_hardware_modules.close = lambda: closed.append(True)  # type: ignore[method-assign]

    provider.close()

    assert closed == [True]
