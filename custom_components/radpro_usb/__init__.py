"""Rad Pro USB integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BAUDRATE,
    CONF_COMMANDS,
    CONF_ENABLE_DERIVED,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_COMMANDS,
    DEFAULT_ENABLE_DERIVED,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import RadProCoordinator
from .radpro_serial import RadProSerial

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = {
        CONF_BAUDRATE: entry.data[CONF_BAUDRATE],
        CONF_TIMEOUT: entry.data[CONF_TIMEOUT],
        CONF_SCAN_INTERVAL: entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        CONF_COMMANDS: entry.options.get(CONF_COMMANDS, DEFAULT_COMMANDS),
        CONF_ENABLE_DERIVED: entry.options.get(
            CONF_ENABLE_DERIVED, DEFAULT_ENABLE_DERIVED
        ),
    }

    device = RadProSerial(
        port=entry.data[CONF_PORT],
        baudrate=entry.data[CONF_BAUDRATE],
        timeout=entry.data[CONF_TIMEOUT],
    )
    coordinator = RadProCoordinator(hass, device, data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "device": device,
        "commands": data[CONF_COMMANDS],
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if entry_data:
            coordinator = entry_data.get("coordinator")
            if coordinator:
                coordinator.close()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
