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
DEFAULT_COMMANDS: Final = ["tubeRate", "tubePulseCount", "doseRate"]
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


KNOWN_COMMANDS: Final = {
    "tubeRate": CommandInfo(
        name="Tube Rate",
        unit="CPM",
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
    "doseRate": CommandInfo(
        name="Dose Rate",
        unit="uSv/h",
        state_class="measurement",
        device_class=None,
        icon="mdi:radioactive",
        value_type=float,
    ),
    "deviceId": CommandInfo(
        name="Device Id",
        unit=None,
        state_class=None,
        device_class=None,
        icon="mdi:identifier",
        value_type=str,
    ),
}

DERIVED_CPS_KEY: Final = "derived_cps"
DERIVED_CPM_KEY: Final = "derived_cpm"
