"""Config flow for Rad Pro USB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import (
    CONF_BAUDRATE,
    CONF_ENABLE_DERIVED,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_BAUDRATE,
    DEFAULT_ENABLE_DERIVED,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    RADPRO_VIDPID,
)

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - handled at runtime by requirements
    list_ports = None


@dataclass(frozen=True)
class _DetectedPort:
    device: str
    label: str


def _is_radpro_port(port) -> bool:
    """Return True if the serial port looks like a Rad Pro device.

    Args:
        port: pyserial ListPortInfo-like object with USB metadata.

    Returns:
        True when VID/PID or descriptors match Rad Pro patterns.
    """
    # Prefer VID/PID allowlist to avoid false positives.
    if port.vid is not None and port.pid is not None:
        if (port.vid, port.pid) in RADPRO_VIDPID:
            return True
    # Fallback to product/description heuristics for adapters without VID/PID.
    text = " ".join(
        item for item in (port.product, port.description, port.manufacturer) if item
    ).lower()
    return "rad pro" in text or "radpro" in text


def _port_label(port) -> str:
    """Build a user-friendly label for a serial port.

    Args:
        port: pyserial ListPortInfo-like object.

    Returns:
        A label including device path and identifying details.
    """
    # Prefer product name, then description, then manufacturer.
    details: list[str] = []
    if port.product:
        details.append(port.product)
    elif port.description and port.description != port.device:
        details.append(port.description)
    elif port.manufacturer:
        details.append(port.manufacturer)
    # Append VID/PID for quick identification in UI.
    if port.vid is not None and port.pid is not None:
        details.append(f"{port.vid:04x}:{port.pid:04x}")
    if details:
        return f"{port.device} ({', '.join(details)})"
    return port.device


def _list_radpro_ports() -> list[_DetectedPort]:
    """Enumerate Rad Pro serial ports with labels.

    Returns:
        A sorted list of detected Rad Pro ports.
    """
    if list_ports is None:
        return []
    ports: list[_DetectedPort] = []
    seen: set[str] = set()
    for port in list_ports.comports():
        if not _is_radpro_port(port):
            continue
        if not port.device or port.device in seen:
            continue
        # Deduplicate by device path to avoid duplicate entries.
        seen.add(port.device)
        ports.append(_DetectedPort(device=port.device, label=_port_label(port)))
    return sorted(ports, key=lambda item: item.device)


def _suggested_port(ports: list[_DetectedPort]) -> str | None:
    """Return a suggested port value for the config flow.

    Args:
        ports: Detected Rad Pro ports.

    Returns:
        The first port device path, or None.
    """
    return ports[0].device if ports else None


def _timeout_field():
    """Return a timeout field compatible with multiple HA selector versions.

    Returns:
        A NumberSelector when available, otherwise a float coercion validator.
    """
    if hasattr(selector, "NumberSelector") and hasattr(selector, "NumberSelectorConfig"):
        mode = getattr(getattr(selector, "NumberSelectorMode", None), "BOX", None)
        if mode is not None:
            return selector.NumberSelector(
                selector.NumberSelectorConfig(
                    step=0.1,
                    mode=mode,
                    unit_of_measurement="s",
                )
            )
    # Fallback for older Home Assistant versions without NumberSelector.
    return vol.Coerce(float)


class RadProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rad Pro USB."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial configuration step.

        Args:
            user_input: Optional user-provided form data.

        Returns:
            A Home Assistant flow result.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(port)
            self._abort_if_unique_id_configured()

            options = {
                CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                CONF_ENABLE_DERIVED: user_input[CONF_ENABLE_DERIVED],
            }
            data = {
                CONF_PORT: port,
                CONF_BAUDRATE: user_input[CONF_BAUDRATE],
                CONF_TIMEOUT: user_input[CONF_TIMEOUT],
            }
            title = f"Rad Pro ({port})"
            return self.async_create_entry(title=title, data=data, options=options)

        ports = await self.hass.async_add_executor_job(_list_radpro_ports)
        suggested = _suggested_port(ports)
        if ports:
            options = [{"value": port.device, "label": port.label} for port in ports]
            port_selector = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=options, mode=selector.SelectSelectorMode.DROPDOWN
                )
            )
        else:
            port_selector = str
        timeout_selector = _timeout_field()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_PORT, default=suggested or ""): port_selector,
                vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): int,
                vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): timeout_selector,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
                vol.Required(
                    CONF_ENABLE_DERIVED, default=DEFAULT_ENABLE_DERIVED
                ): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, user_input: dict[str, Any]):
        """Handle configuration via YAML import.

        Args:
            user_input: Data imported from configuration.yaml.

        Returns:
            A Home Assistant flow result.
        """
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler.

        Args:
            config_entry: Active config entry.

        Returns:
            Options flow handler instance.
        """
        return RadProOptionsFlow(config_entry)


class RadProOptionsFlow(config_entries.OptionsFlow):
    """Handle Rad Pro USB options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow.

        Args:
            entry: Active config entry.
        """
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle the options flow.

        Args:
            user_input: Optional user-provided form data.

        Returns:
            A Home Assistant flow result.
        """
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_ENABLE_DERIVED: user_input[CONF_ENABLE_DERIVED],
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self._entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): int,
                vol.Required(
                    CONF_ENABLE_DERIVED,
                    default=self._entry.options.get(
                        CONF_ENABLE_DERIVED, DEFAULT_ENABLE_DERIVED
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
