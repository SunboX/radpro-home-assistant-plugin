"""Data update coordinator for Rad Pro USB."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COMMANDS,
    CONF_ENABLE_DERIVED,
    CONF_SCAN_INTERVAL,
    DERIVED_CPM_KEY,
    DERIVED_CPS_KEY,
)
from .radpro_serial import RadProError, RadProSerial

_LOGGER = logging.getLogger(__name__)


@dataclass
class RadProData:
    """Container for Rad Pro data."""

    values: dict[str, float | int | str]


class RadProCoordinator(DataUpdateCoordinator[RadProData]):
    """Coordinator handling serial polling."""

    def __init__(self, hass: HomeAssistant, device: RadProSerial, entry_data: dict) -> None:
        self._device = device
        self._commands: list[str] = entry_data[CONF_COMMANDS]
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
    def commands(self) -> list[str]:
        return list(self._commands)

    @property
    def enable_derived(self) -> bool:
        return self._enable_derived

    async def _async_update_data(self) -> RadProData:
        try:
            values = await self.hass.async_add_executor_job(self._poll_device)
        except RadProError as err:
            raise UpdateFailed(str(err)) from err
        return RadProData(values=values)

    def _poll_device(self) -> dict[str, float | int | str]:
        values: dict[str, float | int | str] = {}
        for command in self._commands:
            try:
                response = self._device.query_value(f"GET {command}")
                values[command] = response.value
            except RadProError as err:
                _LOGGER.debug("Rad Pro command %s failed: %s", command, err)

        if self._enable_derived:
            self._update_derived(values)
        return values

    def _update_derived(self, values: dict[str, float | int | str]) -> None:
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
        self._device.close()
