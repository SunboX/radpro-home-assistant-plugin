"""Constants for Rad Pro USB integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DOMAIN: Final = "radpro_usb"

CONF_BAUDRATE: Final = "baudrate"
CONF_TIMEOUT: Final = "timeout"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_COMMANDS: Final = "commands"
CONF_ENABLE_DERIVED: Final = "enable_derived"
CONF_PORT: Final = "port"

DEFAULT_BAUDRATE: Final = 115200
DEFAULT_TIMEOUT: Final = 1.0
DEFAULT_SCAN_INTERVAL: Final = 5
# Query list mirrors the WiFi bridge MQTT publish set.
DEFAULT_QUERY_COMMANDS: Final = [
    "deviceId",
    "devicePower",
    "deviceBatteryVoltage",
    "deviceTime",
    "deviceTimeZone",
    "tubeSensitivity",
    "tubeTime",
    "tubeDeadTime",
    "tubeDeadTimeCompensation",
    "tubeHVFrequency",
    "tubeHVDutyCycle",
    "tubePulseCount",
    "tubeRate",
]
DEFAULT_COMMANDS: Final = DEFAULT_QUERY_COMMANDS

# Map raw command names to the keys exposed as HA sensors.
COMMAND_KEY_MAP: Final = {
    "deviceId": "deviceId",
    "devicePower": "devicePower",
    "deviceBatteryVoltage": "deviceBatteryVoltage",
    "deviceTime": "deviceTime",
    "deviceTimeZone": "deviceTimeZone",
    "tubeSensitivity": "tubeSensitivity",
    "tubeTime": "tubeLifetime",
    "tubeDeadTime": "tubeDeadTime",
    "tubeDeadTimeCompensation": "tubeDeadTimeCompensation",
    "tubeHVFrequency": "tubeHvFrequency",
    "tubeHVDutyCycle": "tubeHvDutyCycle",
    "tubePulseCount": "tubePulseCount",
    "tubeRate": "tubeRate",
}

DEFAULT_SENSOR_KEYS: Final = [
    "deviceId",
    "deviceModel",
    "deviceFirmware",
    "deviceLocale",
    "devicePower",
    "deviceBatteryVoltage",
    "deviceBatteryPercent",
    "deviceTime",
    "deviceTimeZone",
    "tubeSensitivity",
    "tubeLifetime",
    "tubeDeadTime",
    "tubeDeadTimeCompensation",
    "tubeHvFrequency",
    "tubeHvDutyCycle",
    "tubePulseCount",
    "tubeRate",
    "tubeDoseRate",
]

BINARY_SENSOR_KEYS: Final = {"devicePower"}
# Avoid cluttering the activity log with fast-changing diagnostics.
DEFAULT_DISABLED_KEYS: Final = {"deviceTime"}
DEFAULT_ENABLE_DERIVED: Final = False

RADPRO_VIDPID: Final = {
    (0x0483, 0x5740),
    (0x1A86, 0x7523),
}


@dataclass(frozen=True)
class CommandInfo:
    """Metadata for a Rad Pro command."""

    name: str
    unit: str | None
    state_class: str | None
    device_class: str | None
    icon: str | None
    value_type: type | None
    entity_category: str | None = None


KNOWN_COMMANDS: Final = {
    "deviceId": CommandInfo(
        name="Device ID",
        unit=None,
        state_class=None,
        device_class=None,
        icon="mdi:identifier",
        value_type=str,
        entity_category="diagnostic",
    ),
    "deviceModel": CommandInfo(
        name="Device Model",
        unit=None,
        state_class=None,
        device_class=None,
        icon="mdi:information-outline",
        value_type=str,
        entity_category="diagnostic",
    ),
    "deviceFirmware": CommandInfo(
        name="Device Firmware",
        unit=None,
        state_class=None,
        device_class=None,
        icon="mdi:chip",
        value_type=str,
        entity_category="diagnostic",
    ),
    "deviceLocale": CommandInfo(
        name="Device Locale",
        unit=None,
        state_class=None,
        device_class=None,
        icon="mdi:translate",
        value_type=str,
        entity_category="diagnostic",
    ),
    "devicePower": CommandInfo(
        name="Power",
        unit=None,
        state_class=None,
        device_class="power",
        icon="mdi:power-plug",
        value_type=bool,
    ),
    "deviceBatteryVoltage": CommandInfo(
        name="Battery Voltage",
        unit="V",
        state_class="measurement",
        device_class="voltage",
        icon="mdi:flash",
        value_type=float,
    ),
    "deviceBatteryPercent": CommandInfo(
        name="Battery",
        unit="%",
        state_class="measurement",
        device_class="battery",
        icon="mdi:battery",
        value_type=int,
    ),
    "deviceTime": CommandInfo(
        name="Device Time",
        unit=None,
        state_class=None,
        device_class="timestamp",
        icon="mdi:clock-outline",
        value_type=int,
        entity_category="diagnostic",
    ),
    "deviceTimeZone": CommandInfo(
        name="Device Time Zone",
        unit=None,
        state_class=None,
        device_class=None,
        icon="mdi:map-clock",
        value_type=str,
        entity_category="diagnostic",
    ),
    "tubeRate": CommandInfo(
        name="Tube Rate",
        unit="cpm",
        state_class="measurement",
        device_class=None,
        icon="mdi:radioactive",
        value_type=float,
    ),
    "tubePulseCount": CommandInfo(
        name="Tube Pulse Count",
        unit="count",
        state_class="total_increasing",
        device_class=None,
        icon="mdi:pulse",
        value_type=int,
    ),
    "tubeDoseRate": CommandInfo(
        name="Dose Rate",
        unit="uSv/h",
        state_class="measurement",
        device_class=None,
        icon="mdi:radioactive",
        value_type=float,
    ),
    "tubeSensitivity": CommandInfo(
        name="Tube Sensitivity",
        unit="cpm/uSv/h",
        state_class=None,
        device_class=None,
        icon="mdi:tune-vertical",
        value_type=float,
    ),
    "tubeLifetime": CommandInfo(
        name="Tube Lifetime",
        unit="s",
        state_class=None,
        device_class=None,
        icon="mdi:timer-sand",
        value_type=int,
        entity_category="diagnostic",
    ),
    "tubeDeadTime": CommandInfo(
        name="Tube Dead Time",
        unit="s",
        state_class=None,
        device_class=None,
        icon="mdi:timer",
        value_type=float,
    ),
    "tubeDeadTimeCompensation": CommandInfo(
        name="Tube Dead Time Compensation",
        unit="s",
        state_class=None,
        device_class=None,
        icon="mdi:timer-sync",
        value_type=float,
    ),
    "tubeHvFrequency": CommandInfo(
        name="Tube HV Frequency",
        unit="Hz",
        state_class="measurement",
        device_class="frequency",
        icon="mdi:waveform",
        value_type=float,
    ),
    "tubeHvDutyCycle": CommandInfo(
        name="Tube HV Duty Cycle",
        unit=None,
        state_class=None,
        device_class=None,
        icon="mdi:sine-wave",
        value_type=float,
    ),
}


KNOWN_BINARY_SENSORS: Final = {
    "devicePower": CommandInfo(
        name="Power",
        unit=None,
        state_class=None,
        device_class="power",
        icon="mdi:power-plug",
        value_type=bool,
    )
}

DERIVED_CPS_KEY: Final = "derived_cps"
DERIVED_CPM_KEY: Final = "derived_cpm"
