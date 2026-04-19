"""Rad Pro USB integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_BAUDRATE,
    CONF_DEVICE_ID,
    CONF_ENABLE_DERIVED,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_POLL_COMMANDS,
    DEFAULT_STATIC_COMMANDS,
    DEFAULT_SENSOR_KEYS,
    DEFAULT_ENABLE_DERIVED,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import RadProCoordinator
from .identity import (
    RadProDeviceIdentity,
    describe_entry_updates,
    list_radpro_ports,
    resolve_device_identity,
)
from .radpro_serial import RadProError, RadProSerial

PLATFORMS: list[str] = ["sensor", "binary_sensor"]


def _stored_device_id(entry: ConfigEntry) -> str | None:
    """Return the stable physical counter ID stored for a config entry.

    Args:
        entry: Config entry being set up.

    Returns:
        Stored Rad Pro ``deviceId`` or ``None`` for legacy port-based entries.
    """
    stored = entry.data.get(CONF_DEVICE_ID)
    if isinstance(stored, str) and stored:
        return stored

    # Legacy versions used the serial path as the unique ID.
    if isinstance(entry.unique_id, str) and entry.unique_id != entry.data.get(CONF_PORT):
        return entry.unique_id
    return None


def _resolve_identity_for_entry(entry: ConfigEntry) -> RadProDeviceIdentity:
    """Resolve the currently attached port for a configured physical counter.

    Args:
        entry: Config entry being set up.

    Returns:
        Resolved physical identity including the current serial path.
    """
    detected_ports = [port.device for port in list_radpro_ports()]
    return resolve_device_identity(
        saved_port=entry.data[CONF_PORT],
        saved_device_id=_stored_device_id(entry),
        baudrate=entry.data[CONF_BAUDRATE],
        timeout=entry.data[CONF_TIMEOUT],
        detected_ports=detected_ports,
    )


async def _async_prepare_entry_identity(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> RadProDeviceIdentity:
    """Resolve and persist the physical counter identity for a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.

    Returns:
        Resolved physical identity including the current serial path.

    Raises:
        ConfigEntryNotReady: When the configured counter cannot be found.
    """
    try:
        identity = await hass.async_add_executor_job(_resolve_identity_for_entry, entry)
    except RadProError as err:
        raise ConfigEntryNotReady(str(err)) from err

    updates = describe_entry_updates(
        data=entry.data,
        unique_id=entry.unique_id,
        title=entry.title,
        identity=identity,
    )
    if updates is not None:
        # Persist the stable physical identity and any changed USB path in one update.
        hass.config_entries.async_update_entry(
            entry,
            data=updates["data"],
            unique_id=updates["unique_id"],
            title=updates["title"],
        )
    return identity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Rad Pro USB integration from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to set up.

    Returns:
        True when setup succeeds.
    """
    identity = await _async_prepare_entry_identity(hass, entry)
    data = {
        CONF_BAUDRATE: entry.data[CONF_BAUDRATE],
        CONF_TIMEOUT: entry.data[CONF_TIMEOUT],
        CONF_SCAN_INTERVAL: entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        CONF_ENABLE_DERIVED: entry.options.get(
            CONF_ENABLE_DERIVED, DEFAULT_ENABLE_DERIVED
        ),
        # Keep command and sensor sets aligned with the bridge MQTT payloads.
        "poll_commands": DEFAULT_POLL_COMMANDS,
        "static_commands": DEFAULT_STATIC_COMMANDS,
        "sensor_keys": DEFAULT_SENSOR_KEYS,
    }

    device = RadProSerial(
        port=identity.port,
        baudrate=entry.data[CONF_BAUDRATE],
        timeout=entry.data[CONF_TIMEOUT],
    )
    coordinator = RadProCoordinator(hass, device, data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "device": device,
        "device_id": identity.device_id,
        "port": identity.port,
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
