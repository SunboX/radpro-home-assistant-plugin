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
    DEFAULT_DISABLED_KEYS,
    DOMAIN,
    KNOWN_COMMANDS,
    SENSOR_TRANSLATION_KEYS,
    CommandInfo,
)
from .coordinator import RadProCoordinator


_CAMEL_RE = re.compile(r"([a-z])([A-Z])")


@dataclass(frozen=True)
class _RadProEntityMeta:
    key: str
    info: CommandInfo
    translation_key: str | None = None
    suggested_precision: int | None = None


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


def _format_lifetime_ymdm(seconds: float | int) -> str:
    """Format tube lifetime seconds into years, months, days, minutes.

    Args:
        seconds: Lifetime in seconds.

    Returns:
        Human-readable duration (e.g., "1y 2mo 3d 4m").
    """
    # Use fixed 365-day years and 30-day months for readability.
    total_minutes = int(seconds // 60)
    minutes_per_day = 60 * 24
    minutes_per_month = minutes_per_day * 30
    minutes_per_year = minutes_per_day * 365

    years, remainder = divmod(total_minutes, minutes_per_year)
    months, remainder = divmod(remainder, minutes_per_month)
    days, minutes = divmod(remainder, minutes_per_day)

    parts: list[str] = []
    if years:
        parts.append(f"{years}y")
    if months:
        parts.append(f"{months}mo")
    if days:
        parts.append(f"{days}d")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return " ".join(parts)


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
        translation_key = SENSOR_TRANSLATION_KEYS.get(command)
        entities.append(
            RadProSensor(
                coordinator=coordinator,
                meta=_RadProEntityMeta(
                    key=command, info=info, translation_key=translation_key
                ),
                port=port,
                entry_id=entry.entry_id,
                name_prefix=entry.title,
            )
        )

    if coordinator.enable_derived:
        # Derived sensors are opt-in because they are computed, not device-reported.
        for key, name, unit, precision in (
            (DERIVED_CPS_KEY, "Derived CPS", "CPS", 3),
            (DERIVED_CPM_KEY, "Derived CPM", "CPM", 2),
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
                    meta=_RadProEntityMeta(
                        key=key,
                        info=info,
                        translation_key=SENSOR_TRANSLATION_KEYS.get(key),
                        suggested_precision=precision,
                    ),
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
        if meta.translation_key:
            self._attr_translation_key = meta.translation_key
        else:
            self._attr_name = self._info.name
        self._attr_icon = self._info.icon
        self._attr_native_unit_of_measurement = self._info.unit
        self._attr_state_class = _state_class(self._info.state_class)
        if self._info.entity_category:
            self._attr_entity_category = EntityCategory(self._info.entity_category)
        if self._key in DEFAULT_DISABLED_KEYS:
            self._attr_entity_registry_enabled_default = False
        if meta.suggested_precision is not None:
            self._attr_suggested_display_precision = meta.suggested_precision
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
        value = self.coordinator.data.values.get(self._key)
        if self._key == "tubeLifetime" and isinstance(value, (int, float)):
            return _format_lifetime_ymdm(value)
        return value
