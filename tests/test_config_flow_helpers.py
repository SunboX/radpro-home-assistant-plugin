"""Tests for config flow helper utilities."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

pytest.importorskip("homeassistant")

from custom_components.radpro_usb.config_flow import (
    _is_radpro_port,
    _port_label,
    _timeout_field,
)
from homeassistant.helpers import selector as ha_selector
from custom_components.radpro_usb.const import RADPRO_VIDPID


@dataclass
class _StubPort:
    """Minimal stub for pyserial ListPortInfo."""

    device: str
    vid: int | None = None
    pid: int | None = None
    product: str | None = None
    description: str | None = None
    manufacturer: str | None = None


def test_is_radpro_port_matches_vidpid() -> None:
    """Accept ports with known VID/PID pairs."""
    vid, pid = next(iter(RADPRO_VIDPID))
    port = _StubPort(device="/dev/ttyUSB0", vid=vid, pid=pid)
    assert _is_radpro_port(port)


def test_is_radpro_port_matches_name() -> None:
    """Accept ports with Rad Pro naming even without VID/PID."""
    port = _StubPort(
        device="/dev/ttyUSB1",
        product="Rad Pro USB",
        description="USB Serial",
        manufacturer="Bosean",
    )
    assert _is_radpro_port(port)


def test_is_radpro_port_rejects_unknown() -> None:
    """Reject ports that do not match known patterns."""
    port = _StubPort(device="/dev/ttyS0", product="Unrelated Adapter")
    assert not _is_radpro_port(port)


def test_port_label_prefers_product_and_vidpid() -> None:
    """Include product and VID/PID when available."""
    port = _StubPort(
        device="/dev/ttyUSB0",
        product="USB Serial",
        vid=0x1A86,
        pid=0x7523,
    )
    assert _port_label(port) == "/dev/ttyUSB0 (USB Serial, 1a86:7523)"


def test_port_label_falls_back_to_device() -> None:
    """Return the device path when no details exist."""
    port = _StubPort(device="/dev/ttyUSB2")
    assert _port_label(port) == "/dev/ttyUSB2"


def test_timeout_field_compatibility() -> None:
    """Return a selector or validator without raising."""
    field = _timeout_field()
    if hasattr(ha_selector, "NumberSelector"):
        assert field is not None
    else:
        assert callable(field)
