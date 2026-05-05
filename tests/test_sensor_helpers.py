# SPDX-FileCopyrightText: 2026 André Fiedler
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for sensor helper formatting."""

from __future__ import annotations

import pytest

pytest.importorskip("homeassistant")

from custom_components.radpro_usb.sensor import _format_lifetime_ymdm


def test_format_lifetime_zero_minutes() -> None:
    """Return minutes even when duration is below one minute."""
    assert _format_lifetime_ymdm(59) == "0m"


def test_format_lifetime_minutes_and_days() -> None:
    """Format a mix of days and minutes."""
    # 2 days + 3 minutes
    seconds = (2 * 24 * 60 + 3) * 60
    assert _format_lifetime_ymdm(seconds) == "2d 3m"


def test_format_lifetime_years_months_days_minutes() -> None:
    """Format years, months, days, minutes using fixed month length."""
    minutes = (1 * 365 * 24 * 60) + (2 * 30 * 24 * 60) + (3 * 24 * 60) + 4
    seconds = minutes * 60
    assert _format_lifetime_ymdm(seconds) == "1y 2mo 3d 4m"
