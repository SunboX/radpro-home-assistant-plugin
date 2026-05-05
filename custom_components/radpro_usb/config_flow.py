# SPDX-FileCopyrightText: 2026 André Fiedler
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Config flow for Rad Pro USB."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import (
    CONF_BAUDRATE,
    CONF_DEVICE_ID,
    CONF_ENABLE_DERIVED,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_BAUDRATE,
    DEFAULT_ENABLE_DERIVED,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .identity import (
    DetectedPort as _DetectedPort,
    device_title,
    is_radpro_port as _is_radpro_port,
    list_radpro_ports as _list_radpro_ports,
    port_label as _port_label,
    probe_device_identity,
    suggested_port as _suggested_port,
)
from .radpro_serial import RadProError


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
            baudrate = user_input[CONF_BAUDRATE]
            timeout = user_input[CONF_TIMEOUT]
            try:
                identity = await self.hass.async_add_executor_job(
                    probe_device_identity,
                    port,
                    baudrate,
                    timeout,
                )
            except RadProError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(identity.device_id)
                self._abort_if_unique_id_configured()

                options = {
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_ENABLE_DERIVED: user_input[CONF_ENABLE_DERIVED],
                }
                data = {
                    CONF_PORT: port,
                    CONF_BAUDRATE: baudrate,
                    CONF_TIMEOUT: timeout,
                    CONF_DEVICE_ID: identity.device_id,
                }
                return self.async_create_entry(
                    # Reuse the shared title builder so newly added entries match migrated ones.
                    title=device_title(identity.device_id, model=identity.model),
                    data=data,
                    options=options,
                )

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
