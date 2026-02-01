"""Tests for coordinator helper functions."""

from __future__ import annotations

from datetime import timezone

import pytest

pytest.importorskip("homeassistant")

import custom_components.radpro_usb.coordinator as coordinator_module
from custom_components.radpro_usb.const import DERIVED_CPM_KEY, DERIVED_CPS_KEY
from custom_components.radpro_usb.coordinator import (
    RadProCoordinator,
    RadProData,
    _clean_response,
    _parse_device_id,
    _parse_device_power,
    _parse_device_time,
    _parse_device_timezone,
    _update_battery_percent,
    _update_dose_rate,
)


def test_clean_response_strips_ok_prefix() -> None:
    """Strip the OK prefix and surrounding whitespace."""
    assert _clean_response("  OK 123 \r\n") == "123"
    assert _clean_response("OK test") == "test"


def test_parse_device_id_full_payload() -> None:
    """Parse model, firmware, locale, and device ID."""
    payload = "GC-01;3.0.1/EN;ABC123"
    parsed = _parse_device_id(payload)
    assert parsed["deviceModel"] == "GC-01"
    assert parsed["deviceFirmware"] == "3.0.1"
    assert parsed["deviceLocale"] == "EN"
    assert parsed["deviceId"] == "ABC123"


def test_parse_device_id_minimal_payload() -> None:
    """Allow device ID only payloads."""
    parsed = _parse_device_id("ABC123")
    assert parsed == {"deviceId": "ABC123"}


def test_parse_device_time_epoch() -> None:
    """Convert epoch seconds to UTC datetime."""
    ts = 1700000000
    parsed = _parse_device_time(str(ts), ts)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert int(parsed.timestamp()) == ts


def test_parse_device_power_values() -> None:
    """Normalize power payloads to booleans."""
    assert _parse_device_power("1", None) is True
    assert _parse_device_power("0", None) is False
    assert _parse_device_power("ON", None) is True
    assert _parse_device_power("OFF", None) is False
    assert _parse_device_power("", 1) is True


def test_parse_device_timezone_numeric() -> None:
    """Convert numeric offsets to UTC±HH:MM strings."""
    assert _parse_device_timezone("-1.0") == "UTC-01:00"
    assert _parse_device_timezone("2") == "UTC+02:00"
    assert _parse_device_timezone("5.5") == "UTC+05:30"


def test_parse_device_timezone_named() -> None:
    """Preserve named time zones."""
    assert _parse_device_timezone("Europe/Berlin") == "Europe/Berlin"


def test_update_battery_percent() -> None:
    """Compute battery percentage from voltage."""
    values = {"deviceBatteryVoltage": 3.6}
    _update_battery_percent(values)
    assert values["deviceBatteryPercent"] == 50


def test_update_dose_rate() -> None:
    """Compute dose rate from tube rate and sensitivity."""
    values = {"tubeRate": 200, "tubeSensitivity": 100}
    _update_dose_rate(values)
    assert values["tubeDoseRate"] == 2.0


def _make_coord() -> RadProCoordinator:
    """Create a coordinator instance without calling __init__."""
    coord = RadProCoordinator.__new__(RadProCoordinator)
    coord._poll_commands = []
    coord._static_commands = []
    coord._static_completed = set()
    coord.data = None
    coord._enable_derived = False
    coord._last_pulse_count = None
    coord._last_pulse_timestamp = None
    coord._last_cps = None
    coord._last_cpm = None
    return coord


def test_update_derived_keeps_last_value(monkeypatch) -> None:
    """Keep last derived values when no new pulses arrive."""
    coord = _make_coord()
    coord._last_pulse_count = 100
    coord._last_pulse_timestamp = 0.0
    coord._last_cps = 0.2
    coord._last_cpm = 12.0

    monkeypatch.setattr(coordinator_module.time, "monotonic", lambda: 10.0)
    values = {"tubePulseCount": 100}
    coord._update_derived(values)

    assert values[DERIVED_CPS_KEY] == 0.2
    assert values[DERIVED_CPM_KEY] == 12.0
    assert coord._last_pulse_timestamp == 0.0


def test_update_derived_rounds_values(monkeypatch) -> None:
    """Round derived values to avoid excessive decimals."""
    coord = _make_coord()
    coord._last_pulse_count = 100
    coord._last_pulse_timestamp = 0.0

    monkeypatch.setattr(coordinator_module.time, "monotonic", lambda: 5.0)
    values = {"tubePulseCount": 101}
    coord._update_derived(values)

    assert values[DERIVED_CPS_KEY] == 0.2
    assert values[DERIVED_CPM_KEY] == 12.0


def test_static_values_are_retained() -> None:
    """Retain static values when they are not re-polled."""
    coord = _make_coord()
    coord._poll_commands = []
    coord._static_commands = ["deviceTime"]
    coord._static_completed = {"deviceTime"}
    coord._device = None

    prev = RadProData(values={"deviceTime": _parse_device_time("1", 1)})
    coord.data = prev

    values = coord._poll_device()
    assert values["deviceTime"] == prev.values["deviceTime"]
