"""Binary sensor platform for Rad Pro USB."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BINARY_SENSOR_KEYS,
    CONF_PORT,
    DOMAIN,
    KNOWN_BINARY_SENSORS,
)
from .coordinator import RadProCoordinator


@dataclass(frozen=True)
class _RadProBinaryMeta:
    key: str
    name: str
    device_class: str | None
    icon: str | None
    entity_category: str | None


def _command_meta(command: str) -> _RadProBinaryMeta:
    """Return metadata for a binary command key.

    Args:
        command: Command key used in the data dict.

    Returns:
        Metadata describing name, device class, and icon.
    """
    info = KNOWN_BINARY_SENSORS.get(command)
    if not info:
        # Fall back to a simple title if metadata is missing.
        return _RadProBinaryMeta(
            key=command,
            name=command.replace("_", " ").title(),
            device_class=None,
            icon=None,
            entity_category=None,
        )
    return _RadProBinaryMeta(
        key=command,
        name=info.name,
        device_class=info.device_class,
        icon=info.icon,
        entity_category=info.entity_category,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Rad Pro binary sensors from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.
        async_add_entities: Callback to register entities.
    """
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: RadProCoordinator = entry_data["coordinator"]
    sensor_keys: list[str] = entry_data["sensor_keys"]
    port: str = entry.data[CONF_PORT]

    entities: list[RadProBinarySensor] = []
    for command in sensor_keys:
        if command not in BINARY_SENSOR_KEYS:
            continue
        meta = _command_meta(command)
        entities.append(
            RadProBinarySensor(
                coordinator=coordinator,
                meta=meta,
                port=port,
                entry_id=entry.entry_id,
                name_prefix=entry.title,
            )
        )

    async_add_entities(entities)


class RadProBinarySensor(
    CoordinatorEntity[RadProCoordinator], BinarySensorEntity
):
    """Representation of a Rad Pro binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RadProCoordinator,
        meta: _RadProBinaryMeta,
        port: str,
        entry_id: str,
        name_prefix: str,
    ) -> None:
        """Initialize a Rad Pro binary sensor entity.

        Args:
            coordinator: Shared data coordinator.
            meta: Metadata for the command key.
            port: Serial device path.
            entry_id: Config entry ID.
            name_prefix: Device name prefix for the entity.
        """
        super().__init__(coordinator)
        self._key = meta.key
        self._attr_unique_id = f"{entry_id}_{self._key}"
        self._attr_name = meta.name
        if meta.device_class:
            self._attr_device_class = BinarySensorDeviceClass(meta.device_class)
        self._attr_icon = meta.icon
        if meta.entity_category:
            self._attr_entity_category = EntityCategory(meta.entity_category)
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
    def is_on(self) -> bool | None:
        """Return the current on/off state, normalized to bool when possible."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.values.get(self._key)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(int(value))
        if isinstance(value, str):
            upper = value.strip().upper()
            if upper in {"1", "ON", "TRUE"}:
                return True
            if upper in {"0", "OFF", "FALSE"}:
                return False
        return None
