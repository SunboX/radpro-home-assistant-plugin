# SPDX-FileCopyrightText: 2026 André Fiedler
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serial client for Rad Pro devices."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Any

import serial
from serial import SerialException


NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


class RadProError(Exception):
    """Raised when the Rad Pro device returns an error or times out."""


@dataclass
class RadProResponse:
    """Parsed response from the device."""

    raw: str
    value: Any


class RadProSerial:
    """Talks to a Rad Pro over USB serial."""

    def __init__(
        self,
        port: str,
        baudrate: int,
        timeout: float,
        eol: str = "\r\n",
    ) -> None:
        """Initialize the serial client.

        Args:
            port: Serial device path.
            baudrate: Baud rate for the connection.
            timeout: Read/write timeout in seconds.
            eol: Line ending to append to commands.
        """
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._eol = eol
        self._serial: serial.Serial | None = None
        self._lock = threading.Lock()

    @property
    def port(self) -> str:
        """Return the configured serial port path."""
        return self._port

    def close(self) -> None:
        """Close the serial port if it is open."""
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.close()

    def _ensure_open(self) -> None:
        """Open the serial port if it is not already open."""
        if self._serial and self._serial.is_open:
            return
        # Use write timeout to avoid blocking forever on cable issues.
        self._serial = serial.Serial(
            self._port,
            self._baudrate,
            timeout=self._timeout,
            write_timeout=self._timeout,
        )

    def query(self, command: str, max_lines: int = 6) -> RadProResponse:
        """Send a command and parse the first usable response line.

        Args:
            command: Command string without EOL.
            max_lines: Maximum number of response lines to scan.

        Returns:
            Parsed RadProResponse with raw line and value.

        Raises:
            RadProError: When communication fails or no response is parsed.
        """
        with self._lock:
            try:
                self._ensure_open()
            except SerialException as err:
                raise RadProError(f"Failed to open serial port {self._port}: {err}") from err

            assert self._serial is not None
            try:
                self._serial.reset_input_buffer()
            except SerialException:
                # Some adapters do not support reset; ignore.
                pass

            payload = f"{command}{self._eol}".encode("ascii", errors="ignore")
            try:
                self._serial.write(payload)
                self._serial.flush()
            except SerialException as err:
                raise RadProError(f"Failed to write command {command}: {err}") from err

            response_lines: list[str] = []
            for _ in range(max_lines):
                try:
                    raw = self._serial.readline()
                except SerialException as err:
                    raise RadProError(f"Serial read error: {err}") from err

                if not raw:
                    continue
                line = raw.decode(errors="ignore").strip()
                if not line:
                    continue
                response_lines.append(line)
                upper = line.upper()
                if upper.startswith("ERR") or "ERROR" in upper:
                    raise RadProError(f"Device error: {line}")
                if line.startswith("GET "):
                    continue
                value = self._parse_value(line)
                return RadProResponse(raw=line, value=value)

            if response_lines:
                raise RadProError("No parsable response")
            raise RadProError("No response")

    def query_value(self, command: str) -> RadProResponse:
        """Convenience wrapper for query().

        Args:
            command: Command string without EOL.

        Returns:
            Parsed RadProResponse.
        """
        return self.query(command)

    @staticmethod
    def _parse_value(line: str) -> Any:
        """Parse a numeric value from a response line when possible.

        Args:
            line: Raw line from the device.

        Returns:
            int, float, or the original string when no number is found.
        """
        match = NUMBER_RE.search(line)
        if not match:
            return line
        value = match.group(0)
        if "." in value or "e" in value.lower():
            try:
                return float(value)
            except ValueError:
                return value
        try:
            return int(value)
        except ValueError:
            return value
