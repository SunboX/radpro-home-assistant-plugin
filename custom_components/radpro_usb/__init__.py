"""Rad Pro USB integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BAUDRATE,
    CONF_ENABLE_DERIVED,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_QUERY_COMMANDS,
    DEFAULT_SENSOR_KEYS,
    DEFAULT_ENABLE_DERIVED,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import RadProCoordinator
from .radpro_serial import RadProSerial

PLATFORMS: list[str] = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Rad Pro USB integration from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to set up.

    Returns:
        True when setup succeeds.
    """
    data = {
        CONF_BAUDRATE: entry.data[CONF_BAUDRATE],
        CONF_TIMEOUT: entry.data[CONF_TIMEOUT],
        CONF_SCAN_INTERVAL: entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        CONF_ENABLE_DERIVED: entry.options.get(
            CONF_ENABLE_DERIVED, DEFAULT_ENABLE_DERIVED
        ),
        # Keep command and sensor sets aligned with the bridge MQTT payloads.
        "query_commands": DEFAULT_QUERY_COMMANDS,
        "sensor_keys": DEFAULT_SENSOR_KEYS,
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
        "sensor_keys": data["sensor_keys"],
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Rad Pro USB config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to unload.

    Returns:
        True when unload succeeds.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if entry_data:
            coordinator = entry_data.get("coordinator")
            if coordinator:
                coordinator.close()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change.

    Args:
        hass: Home Assistant instance.
        entry: Updated config entry.
    """
    await hass.config_entries.async_reload(entry.entry_id)
