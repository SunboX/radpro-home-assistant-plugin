# SPDX-FileCopyrightText: 2026 André Fiedler
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for Rad Pro identity and rebinding helpers."""

from __future__ import annotations

import pytest

from custom_components.radpro_usb.identity import (
    RadProDeviceIdentity,
    describe_entry_updates,
    device_title,
    resolve_device_identity,
)
from custom_components.radpro_usb.radpro_serial import RadProError


def test_device_title_uses_model_when_available() -> None:
    """Prefer the probed device model when building the entry title."""
    assert (
        device_title("ABC123", model="Bosean FS-5000")
        == "Bosean FS-5000 (ABC123)"
    )


def test_device_title_falls_back_when_model_is_missing() -> None:
    """Use the legacy Rad Pro prefix when the probe returns no usable model."""
    assert device_title("ABC123", model="  ") == "Rad Pro (ABC123)"


def test_resolve_device_identity_uses_saved_port_when_it_matches() -> None:
    """Keep the saved USB path when it still points at the same counter."""

    def _probe(port: str, baudrate: int, timeout: float) -> RadProDeviceIdentity:
        """Return a deterministic probe result for the selected port."""
        assert baudrate == 115200
        assert timeout == 1.0
        return RadProDeviceIdentity(device_id="ABC123", port=port)

    resolved = resolve_device_identity(
        saved_port="/dev/ttyUSB0",
        saved_device_id="ABC123",
        baudrate=115200,
        timeout=1.0,
        detected_ports=["/dev/ttyUSB0", "/dev/ttyUSB1"],
        probe_port=_probe,
    )

    assert resolved.port == "/dev/ttyUSB0"
    assert resolved.device_id == "ABC123"


def test_resolve_device_identity_rebinds_when_saved_port_has_other_counter() -> None:
    """Scan other detected ports until the saved physical counter is found."""

    def _probe(port: str, baudrate: int, timeout: float) -> RadProDeviceIdentity:
        """Return a per-port physical identity for rebinding checks."""
        del baudrate, timeout
        identities = {
            "/dev/ttyUSB0": RadProDeviceIdentity(device_id="OTHER999", port=port),
            "/dev/ttyUSB1": RadProDeviceIdentity(device_id="ABC123", port=port),
        }
        return identities[port]

    resolved = resolve_device_identity(
        saved_port="/dev/ttyUSB0",
        saved_device_id="ABC123",
        baudrate=115200,
        timeout=1.0,
        detected_ports=["/dev/ttyUSB0", "/dev/ttyUSB1"],
        probe_port=_probe,
    )

    assert resolved.port == "/dev/ttyUSB1"
    assert resolved.device_id == "ABC123"


def test_resolve_device_identity_migrates_legacy_entry_from_saved_port() -> None:
    """Legacy entries without stored device ID should adopt the probed counter."""

    def _probe(port: str, baudrate: int, timeout: float) -> RadProDeviceIdentity:
        """Return the probed device identity for the legacy saved port."""
        del baudrate, timeout
        return RadProDeviceIdentity(device_id="ABC123", port=port)

    resolved = resolve_device_identity(
        saved_port="/dev/ttyUSB0",
        saved_device_id=None,
        baudrate=115200,
        timeout=1.0,
        detected_ports=["/dev/ttyUSB0"],
        probe_port=_probe,
    )

    assert resolved.port == "/dev/ttyUSB0"
    assert resolved.device_id == "ABC123"


def test_resolve_device_identity_raises_when_saved_counter_is_not_attached() -> None:
    """Fail cleanly when no attached port matches the configured counter."""

    def _probe(port: str, baudrate: int, timeout: float) -> RadProDeviceIdentity:
        """Return identities that do not match the requested counter."""
        del baudrate, timeout
        return RadProDeviceIdentity(device_id=f"{port}-id", port=port)

    with pytest.raises(RadProError, match="ABC123"):
        resolve_device_identity(
            saved_port="/dev/ttyUSB0",
            saved_device_id="ABC123",
            baudrate=115200,
            timeout=1.0,
            detected_ports=["/dev/ttyUSB0", "/dev/ttyUSB1"],
            probe_port=_probe,
        )


def test_describe_entry_updates_migrates_legacy_port_bound_entry() -> None:
    """Switch legacy entries from USB-path identity to physical-counter identity."""
    updates = describe_entry_updates(
        data={"port": "/dev/ttyUSB0", "baudrate": 115200, "timeout": 1.0},
        unique_id="/dev/ttyUSB0",
        title="Rad Pro (/dev/ttyUSB0)",
        identity=RadProDeviceIdentity(
            device_id="ABC123",
            port="/dev/ttyUSB1",
            model="Bosean FS-5000",
        ),
    )

    assert updates["unique_id"] == "ABC123"
    assert updates["title"] == "Bosean FS-5000 (ABC123)"
    assert updates["data"]["device_id"] == "ABC123"
    assert updates["data"]["port"] == "/dev/ttyUSB1"


def test_describe_entry_updates_returns_none_when_entry_is_already_current() -> None:
    """Avoid unnecessary config-entry writes when nothing changed."""
    updates = describe_entry_updates(
        data={
            "port": "/dev/ttyUSB0",
            "baudrate": 115200,
            "timeout": 1.0,
            "device_id": "ABC123",
        },
        unique_id="ABC123",
        title="Bosean FS-5000 (ABC123)",
        identity=RadProDeviceIdentity(
            device_id="ABC123",
            port="/dev/ttyUSB0",
            model="Bosean FS-5000",
        ),
    )

    assert updates is None
