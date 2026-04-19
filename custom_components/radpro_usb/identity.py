"""Identity and USB discovery helpers for Rad Pro counters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from .const import RADPRO_VIDPID

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - handled at runtime by requirements
    list_ports = None


@dataclass(frozen=True)
class DetectedPort:
    """Detected USB serial port that looks like a Rad Pro counter."""

    device: str
    label: str

from .radpro_serial import RadProError, RadProSerial


@dataclass(frozen=True)
class RadProDeviceIdentity:
    """Stable identity details for a physical Rad Pro counter."""

    device_id: str
    port: str
    model: str | None = None
    firmware: str | None = None
    locale: str | None = None


def is_radpro_port(port) -> bool:
    """Return ``True`` when a serial port looks like a Rad Pro device.

    Args:
        port: pyserial ``ListPortInfo``-like object with USB metadata.

    Returns:
        ``True`` when the port matches a known VID/PID or Rad Pro descriptors.
    """
    if port.vid is not None and port.pid is not None:
        if (port.vid, port.pid) in RADPRO_VIDPID:
            return True

    text = " ".join(
        item for item in (port.product, port.description, port.manufacturer) if item
    ).lower()
    return "rad pro" in text or "radpro" in text


def port_label(port) -> str:
    """Build a user-friendly label for a detected USB serial port.

    Args:
        port: pyserial ``ListPortInfo``-like object.

    Returns:
        Label including the device path and distinguishing USB details.
    """
    details: list[str] = []
    if port.product:
        details.append(port.product)
    elif port.description and port.description != port.device:
        details.append(port.description)
    elif port.manufacturer:
        details.append(port.manufacturer)

    if port.vid is not None and port.pid is not None:
        details.append(f"{port.vid:04x}:{port.pid:04x}")

    if details:
        return f"{port.device} ({', '.join(details)})"
    return port.device


def list_radpro_ports() -> list[DetectedPort]:
    """Enumerate detected Rad Pro USB serial ports.

    Returns:
        Sorted list of likely Rad Pro serial ports.
    """
    if list_ports is None:
        return []

    ports: list[DetectedPort] = []
    seen: set[str] = set()
    for port in list_ports.comports():
        if not is_radpro_port(port):
            continue
        if not port.device or port.device in seen:
            continue
        # Deduplicate by path to avoid duplicate dropdown items and scan attempts.
        seen.add(port.device)
        ports.append(DetectedPort(device=port.device, label=port_label(port)))
    return sorted(ports, key=lambda item: item.device)


def suggested_port(ports: list[DetectedPort]) -> str | None:
    """Return the default port suggestion for the config flow.

    Args:
        ports: Detected Rad Pro ports.

    Returns:
        First detected serial path or ``None`` when no ports were found.
    """
    return ports[0].device if ports else None


def clean_response(raw: str) -> str:
    """Normalize a device response line.

    Args:
        raw: Raw response line from the device.

    Returns:
        Trimmed response without a leading ``OK `` prefix.
    """
    trimmed = raw.strip()
    if trimmed.upper().startswith("OK "):
        trimmed = trimmed[3:]
    return trimmed.strip()


def parse_device_id_payload(payload: str) -> dict[str, str]:
    """Parse a Rad Pro ``deviceId`` response payload.

    Args:
        payload: Response body without the leading ``OK`` token.

    Returns:
        Parsed identity fields keyed by Home Assistant sensor names.
    """
    if not payload:
        return {}

    parts = [part.strip() for part in payload.split(";")]
    result: dict[str, str] = {}

    # Treat a single-part payload as a bare device ID from older or fallback replies.
    if len(parts) >= 2 and parts[0]:
        result["deviceModel"] = parts[0]

    if len(parts) >= 3:
        firmware_locale = parts[1]
        if firmware_locale:
            if "/" in firmware_locale:
                firmware, locale = firmware_locale.split("/", 1)
                firmware = firmware.strip()
                locale = locale.strip()
                if firmware:
                    result["deviceFirmware"] = firmware
                if locale:
                    result["deviceLocale"] = locale
            else:
                result["deviceFirmware"] = firmware_locale

    device_id = ""
    if len(parts) >= 3:
        device_id = parts[2]
    elif len(parts) == 2:
        device_id = parts[1]
    elif len(parts) == 1:
        device_id = parts[0]

    if device_id:
        result["deviceId"] = device_id
    return result


def device_title(device_id: str) -> str:
    """Build a stable config-entry title for a physical counter.

    Args:
        device_id: Stable Rad Pro device identifier.

    Returns:
        Human-readable config entry title.
    """
    return f"Rad Pro ({device_id})"


def describe_entry_updates(
    data: Mapping[str, Any],
    unique_id: str | None,
    title: str,
    identity: RadProDeviceIdentity,
) -> dict[str, Any] | None:
    """Describe the config-entry updates needed for a resolved counter identity.

    Args:
        data: Existing config-entry data.
        unique_id: Existing config-entry unique ID.
        title: Existing config-entry title.
        identity: Resolved physical counter identity.

    Returns:
        A dict containing updated ``data``, ``unique_id``, and ``title`` values,
        or ``None`` when the entry already matches the resolved counter.
    """
    updated_data = dict(data)
    # Keep transport details mutable while storing the stable physical device ID.
    updated_data["port"] = identity.port
    updated_data["device_id"] = identity.device_id
    updated_title = device_title(identity.device_id)

    if (
        updated_data == dict(data)
        and unique_id == identity.device_id
        and title == updated_title
    ):
        return None

    return {
        "data": updated_data,
        "unique_id": identity.device_id,
        "title": updated_title,
    }


def probe_device_identity(
    port: str,
    baudrate: int,
    timeout: float,
    client_factory: type[RadProSerial] = RadProSerial,
) -> RadProDeviceIdentity:
    """Probe a port and read the physical Rad Pro identity.

    Args:
        port: Serial device path to probe.
        baudrate: Baud rate for the temporary serial connection.
        timeout: Serial timeout in seconds.
        client_factory: Serial client class used for probing.

    Returns:
        The parsed physical identity for the attached counter.

    Raises:
        RadProError: When the port cannot be queried or does not provide a device ID.
    """
    client = client_factory(port=port, baudrate=baudrate, timeout=timeout)
    try:
        response = client.query("GET deviceId")
    finally:
        client.close()

    parsed = parse_device_id_payload(clean_response(response.raw))
    device_id = parsed.get("deviceId")
    if not device_id:
        raise RadProError(f"Device on {port} did not return a deviceId")

    return RadProDeviceIdentity(
        device_id=device_id,
        port=port,
        model=parsed.get("deviceModel"),
        firmware=parsed.get("deviceFirmware"),
        locale=parsed.get("deviceLocale"),
    )


def resolve_device_identity(
    saved_port: str,
    saved_device_id: str | None,
    baudrate: int,
    timeout: float,
    detected_ports: Iterable[str],
    probe_port: Callable[[str, int, float], RadProDeviceIdentity] = probe_device_identity,
) -> RadProDeviceIdentity:
    """Resolve the currently attached port for a configured physical counter.

    Args:
        saved_port: Previously stored serial path.
        saved_device_id: Stable Rad Pro device ID, if already known.
        baudrate: Serial baud rate for probing.
        timeout: Serial timeout in seconds.
        detected_ports: Candidate Rad Pro serial ports to scan.
        probe_port: Injected probe function for tests and setup.

    Returns:
        The matching physical device identity and its currently attached port.

    Raises:
        RadProError: When the configured counter cannot be identified.
    """
    try:
        current_identity = probe_port(saved_port, baudrate, timeout)
    except RadProError:
        current_identity = None

    if current_identity and (
        saved_device_id is None or current_identity.device_id == saved_device_id
    ):
        return current_identity

    if saved_device_id is None:
        raise RadProError(f"Unable to migrate legacy entry on {saved_port}")

    for candidate_port in detected_ports:
        if candidate_port == saved_port:
            continue
        try:
            candidate_identity = probe_port(candidate_port, baudrate, timeout)
        except RadProError:
            # Ignore ports that cannot be opened or do not answer correctly while scanning.
            continue
        if candidate_identity.device_id == saved_device_id:
            return candidate_identity

    raise RadProError(
        f"Unable to find configured Rad Pro counter {saved_device_id} on any detected port"
    )
