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
    CONF_COMMANDS,
    CONF_ENABLE_DERIVED,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_BAUDRATE,
    DEFAULT_COMMANDS,
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
    if port.vid is not None and port.pid is not None:
        if (port.vid, port.pid) in RADPRO_VIDPID:
            return True
    text = " ".join(
        item for item in (port.product, port.description, port.manufacturer) if item
    ).lower()
    return "rad pro" in text or "radpro" in text


def _port_label(port) -> str:
    details: list[str] = []
    if port.product:
        details.append(port.product)
    elif port.description and port.description != port.device:
        details.append(port.description)
    elif port.manufacturer:
        details.append(port.manufacturer)
    if port.vid is not None and port.pid is not None:
        details.append(f"{port.vid:04x}:{port.pid:04x}")
    if details:
        return f"{port.device} ({', '.join(details)})"
    return port.device


def _list_radpro_ports() -> list[_DetectedPort]:
    if list_ports is None:
        return []
    ports: list[_DetectedPort] = []
    seen: set[str] = set()
    for port in list_ports.comports():
        if not _is_radpro_port(port):
            continue
        if not port.device or port.device in seen:
            continue
        seen.add(port.device)
        ports.append(_DetectedPort(device=port.device, label=_port_label(port)))
    return sorted(ports, key=lambda item: item.device)


def _suggested_port(ports: list[_DetectedPort]) -> str | None:
    return ports[0].device if ports else None


def _parse_commands(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


class RadProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rad Pro USB."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(port)
            self._abort_if_unique_id_configured()

            commands = _parse_commands(user_input[CONF_COMMANDS])
            options = {
                CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                CONF_COMMANDS: commands or DEFAULT_COMMANDS,
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

        data_schema = vol.Schema(
            {
                vol.Required(CONF_PORT, default=suggested or ""): port_selector,
                vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): int,
                vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): float,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
                vol.Required(CONF_COMMANDS, default=",".join(DEFAULT_COMMANDS)): str,
                vol.Required(
                    CONF_ENABLE_DERIVED, default=DEFAULT_ENABLE_DERIVED
                ): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, user_input: dict[str, Any]):
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return RadProOptionsFlow(config_entry)


class RadProOptionsFlow(config_entries.OptionsFlow):
    """Handle Rad Pro USB options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            commands = _parse_commands(user_input[CONF_COMMANDS])
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_COMMANDS: commands or DEFAULT_COMMANDS,
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
                    CONF_COMMANDS,
                    default=",".join(
                        self._entry.options.get(CONF_COMMANDS, DEFAULT_COMMANDS)
                    ),
                ): str,
                vol.Required(
                    CONF_ENABLE_DERIVED,
                    default=self._entry.options.get(
                        CONF_ENABLE_DERIVED, DEFAULT_ENABLE_DERIVED
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
