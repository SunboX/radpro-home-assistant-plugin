"""Sensor platform for Rad Pro USB."""

from __future__ import annotations

import re
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BINARY_SENSOR_KEYS,
    CONF_PORT,
    DERIVED_CPM_KEY,
    DERIVED_CPS_KEY,
    DOMAIN,
    KNOWN_COMMANDS,
    CommandInfo,
)
from .coordinator import RadProCoordinator


_CAMEL_RE = re.compile(r"([a-z])([A-Z])")


@dataclass(frozen=True)
class _RadProEntityMeta:
    key: str
    info: CommandInfo


def _titleize(command: str) -> str:
    """Convert a command key into a human-friendly title.

    Args:
        command: Raw command key.

    Returns:
        Title-cased sensor name.
    """
    command = command.replace("_", " ")
    command = _CAMEL_RE.sub(r"\1 \2", command)
    return command.title()


def _command_info(command: str) -> CommandInfo:
    """Return metadata for a command key.

    Args:
        command: Command key used in the data dict.

    Returns:
        CommandInfo with display metadata.
    """
    info = KNOWN_COMMANDS.get(command)
    if info:
        return info
    return CommandInfo(
        name=_titleize(command),
        unit=None,
        state_class="measurement",
        device_class=None,
        icon="mdi:radioactive",
        value_type=None,
    )


def _state_class(value: str | None) -> SensorStateClass | None:
    """Map a state class string to Home Assistant enum.

    Args:
        value: State class string from CommandInfo.

    Returns:
        SensorStateClass or None.
    """
    if value == "measurement":
        return SensorStateClass.MEASUREMENT
    if value == "total_increasing":
        return SensorStateClass.TOTAL_INCREASING
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Rad Pro sensors from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.
        async_add_entities: Callback to register entities.
    """
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: RadProCoordinator = entry_data["coordinator"]
    sensor_keys: list[str] = entry_data["sensor_keys"]
    port: str = entry.data[CONF_PORT]

    entities: list[RadProSensor] = []
    for command in sensor_keys:
        if command in BINARY_SENSOR_KEYS:
            continue
        info = _command_info(command)
        entities.append(
            RadProSensor(
                coordinator=coordinator,
                meta=_RadProEntityMeta(key=command, info=info),
                port=port,
                entry_id=entry.entry_id,
                name_prefix=entry.title,
            )
        )

    if coordinator.enable_derived:
        # Derived sensors are opt-in because they are computed, not device-reported.
        for key, name, unit in (
            (DERIVED_CPS_KEY, "Derived CPS", "CPS"),
            (DERIVED_CPM_KEY, "Derived CPM", "CPM"),
        ):
            info = CommandInfo(
                name=name,
                unit=unit,
                state_class="measurement",
                device_class=None,
                icon="mdi:chart-line",
                value_type=float,
            )
            entities.append(
                RadProSensor(
                    coordinator=coordinator,
                    meta=_RadProEntityMeta(key=key, info=info),
                    port=port,
                    entry_id=entry.entry_id,
                    name_prefix=entry.title,
                )
            )

    async_add_entities(entities)


class RadProSensor(CoordinatorEntity[RadProCoordinator], SensorEntity):
    """Representation of a Rad Pro sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RadProCoordinator,
        meta: _RadProEntityMeta,
        port: str,
        entry_id: str,
        name_prefix: str,
    ) -> None:
        """Initialize a Rad Pro sensor entity.

        Args:
            coordinator: Shared data coordinator.
            meta: Metadata for the command key.
            port: Serial device path.
            entry_id: Config entry ID.
            name_prefix: Device name prefix for the entity.
        """
        super().__init__(coordinator)
        self._key = meta.key
        self._info = meta.info
        self._attr_unique_id = f"{entry_id}_{self._key}"
        self._attr_name = self._info.name
        self._attr_icon = self._info.icon
        self._attr_native_unit_of_measurement = self._info.unit
        self._attr_state_class = _state_class(self._info.state_class)
        if self._info.entity_category:
            self._attr_entity_category = EntityCategory(self._info.entity_category)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name_prefix,
            manufacturer="Rad Pro",
            model="USB",
            configuration_url=None,
            suggested_area="Lab",
        )
        self._attr_extra_state_attributes = {
            "port": port,
            "command": self._key,
        }

    @property
    def available(self) -> bool:
        """Return True when coordinator data contains this key."""
        if not self.coordinator.data:
            return False
        return self._key in self.coordinator.data.values

    @property
    def native_value(self):
        """Return the latest native value for this sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.values.get(self._key)
