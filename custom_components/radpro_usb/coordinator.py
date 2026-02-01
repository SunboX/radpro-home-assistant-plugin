"""Data update coordinator for Rad Pro USB."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENABLE_DERIVED,
    CONF_SCAN_INTERVAL,
    COMMAND_KEY_MAP,
    DERIVED_CPM_KEY,
    DERIVED_CPS_KEY,
)
from .radpro_serial import RadProError, RadProSerial

_LOGGER = logging.getLogger(__name__)


@dataclass
class RadProData:
    """Container for Rad Pro data."""

    values: dict[str, float | int | str | bool | datetime]


class RadProCoordinator(DataUpdateCoordinator[RadProData]):
    """Coordinator handling serial polling."""

    def __init__(self, hass: HomeAssistant, device: RadProSerial, entry_data: dict) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            device: Opened Rad Pro serial client.
            entry_data: Prepared configuration data for polling.
        """
        self._device = device
        self._query_commands: list[str] = entry_data["query_commands"]
        self._enable_derived = entry_data[CONF_ENABLE_DERIVED]
        self._last_pulse_count: int | None = None
        self._last_pulse_timestamp: float | None = None
        super().__init__(
            hass,
            _LOGGER,
            name="radpro_usb",
            update_interval=timedelta(seconds=entry_data[CONF_SCAN_INTERVAL]),
        )

    @property
    def enable_derived(self) -> bool:
        """Return True when derived CPS/CPM sensors are enabled."""
        return self._enable_derived

    async def _async_update_data(self) -> RadProData:
        """Fetch the latest data from the device.

        Returns:
            RadProData containing parsed values.
        """
        try:
            values = await self.hass.async_add_executor_job(self._poll_device)
        except RadProError as err:
            raise UpdateFailed(str(err)) from err
        return RadProData(values=values)

    def _poll_device(self) -> dict[str, float | int | str | bool | datetime]:
        """Poll the device and return parsed values.

        Returns:
            A dict of Home Assistant-friendly keys and values.
        """
        values: dict[str, float | int | str | bool | datetime] = {}
        for command in self._query_commands:
            try:
                response = self._device.query(f"GET {command}")
                raw = response.raw
                cleaned = _clean_response(raw)
                if command == "deviceId":
                    # deviceId payload packs model/firmware/locale/deviceId.
                    values.update(_parse_device_id(cleaned))
                    continue
                if command == "deviceTimeZone":
                    if cleaned:
                        values["deviceTimeZone"] = cleaned
                    continue
                if command == "deviceTime":
                    parsed = _parse_device_time(cleaned, response.value)
                    if parsed is not None:
                        values["deviceTime"] = parsed
                    continue
                if command == "devicePower":
                    parsed = _parse_device_power(cleaned, response.value)
                    if parsed is not None:
                        values["devicePower"] = parsed
                    continue

                # Map raw command names to the keys used for sensors.
                key = COMMAND_KEY_MAP.get(command, command)
                value: Any = response.value
                if isinstance(value, str) and cleaned:
                    value = cleaned
                values[key] = value
            except RadProError as err:
                _LOGGER.debug("Rad Pro command %s failed: %s", command, err)

        # Mirror bridge behavior for computed metrics.
        _update_battery_percent(values)
        _update_dose_rate(values)
        if self._enable_derived:
            self._update_derived(values)
        return values

    def _update_derived(
        self, values: dict[str, float | int | str | bool | datetime]
    ) -> None:
        """Update derived CPS/CPM values using pulse count deltas.

        Args:
            values: Current values dict (mutated in place).
        """
        pulse = values.get("tubePulseCount")
        if not isinstance(pulse, (int, float)):
            return
        now = time.monotonic()
        if self._last_pulse_count is None or self._last_pulse_timestamp is None:
            self._last_pulse_count = int(pulse)
            self._last_pulse_timestamp = now
            return
        delta_count = int(pulse) - self._last_pulse_count
        delta_time = now - self._last_pulse_timestamp
        if delta_time <= 0:
            return
        cps = delta_count / delta_time
        values[DERIVED_CPS_KEY] = cps
        values[DERIVED_CPM_KEY] = cps * 60
        self._last_pulse_count = int(pulse)
        self._last_pulse_timestamp = now

    def close(self) -> None:
        """Close the underlying serial device."""
        self._device.close()


def _clean_response(raw: str) -> str:
    """Normalize a device response line.

    Args:
        raw: Raw response line from the device.

    Returns:
        Trimmed response without a leading "OK " prefix.
    """
    trimmed = raw.strip()
    if trimmed.upper().startswith("OK "):
        trimmed = trimmed[3:]
    return trimmed.strip()


def _parse_device_id(payload: str) -> dict[str, str]:
    """Parse the Rad Pro deviceId response payload.

    Args:
        payload: Response body without "OK " prefix.

    Returns:
        A dict with deviceModel, deviceFirmware, deviceLocale, and deviceId.
    """
    if not payload:
        return {}
    parts = [part.strip() for part in payload.split(";")]
    result: dict[str, str] = {}
    if parts:
        if len(parts[0]):
            result["deviceModel"] = parts[0]
    if len(parts) >= 3:
        firmware_locale = parts[1]
        if firmware_locale:
            if "/" in firmware_locale:
                firmware, locale = firmware_locale.split("/", 1)
                firmware = firmware.strip()
                locale = locale.strip()
                if firmware:
                    result["deviceFirmware"] = firmware
                if locale:
                    result["deviceLocale"] = locale
            else:
                result["deviceFirmware"] = firmware_locale
    device_id = ""
    if len(parts) >= 3:
        device_id = parts[2]
    elif len(parts) == 2:
        device_id = parts[1]
    elif len(parts) == 1:
        device_id = parts[0]
    if device_id:
        result["deviceId"] = device_id
    return result


def _parse_device_time(payload: str, fallback: Any) -> datetime | None:
    """Parse a device time value into a UTC datetime.

    Args:
        payload: String payload from the device.
        fallback: Parsed numeric value from the response parser.

    Returns:
        UTC datetime when value is valid, otherwise None.
    """
    value = None
    if isinstance(fallback, (int, float)):
        value = int(fallback)
    else:
        try:
            value = int(float(payload))
        except (TypeError, ValueError):
            return None
    if value <= 0:
        return None
    # Device reports epoch seconds; expose as UTC timestamp.
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _parse_device_power(payload: str, fallback: Any) -> bool | None:
    """Parse device power responses into a boolean.

    Args:
        payload: Raw payload string from the device.
        fallback: Parsed numeric value from the response parser.

    Returns:
        True/False when parseable, otherwise None.
    """
    if isinstance(fallback, (int, float)):
        return bool(int(fallback))
    upper = payload.strip().upper()
    if upper in {"1", "ON", "TRUE"}:
        return True
    if upper in {"0", "OFF", "FALSE"}:
        return False
    return None


def _update_battery_percent(
    values: dict[str, float | int | str | bool | datetime]
) -> None:
    """Compute battery percent from voltage, clamping to 0-100%.

    Args:
        values: Current values dict (mutated in place).
    """
    voltage = values.get("deviceBatteryVoltage")
    if not isinstance(voltage, (int, float)):
        return
    # Use the same 3.0V-4.2V normalization as the bridge firmware.
    percent = (float(voltage) - 3.0) * (100.0 / (4.2 - 3.0))
    if percent < 0.0:
        percent = 0.0
    if percent > 100.0:
        percent = 100.0
    values["deviceBatteryPercent"] = int(percent + 0.5)


def _update_dose_rate(values: dict[str, float | int | str | bool | datetime]) -> None:
    """Compute dose rate from tube rate and sensitivity.

    Args:
        values: Current values dict (mutated in place).
    """
    rate = values.get("tubeRate")
    sensitivity = values.get("tubeSensitivity")
    if not isinstance(rate, (int, float)):
        return
    if not isinstance(sensitivity, (int, float)) or sensitivity <= 0:
        return
    # Dose rate is tube rate divided by sensitivity (from bridge behavior).
    dose = float(rate) / float(sensitivity)
    values["tubeDoseRate"] = round(dose, 5)
