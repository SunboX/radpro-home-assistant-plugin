# Configuration

Configuration is done through the UI.

## Required
- **Serial port**: The Rad Pro USB device path (recommended: `/dev/serial/by-id/...`).

## Optional
- **Baud rate**: Default `115200`.
- **Serial timeout**: Default `1.0` seconds.
- **Polling interval**: Default `5` seconds.
- **Derived sensors**: Enable CPS/CPM calculated from `tubePulseCount`.

## Multiple counters

- Each config entry represents exactly one physical Rad Pro counter.
- The integration stores the counter's `deviceId` and keeps that as the canonical identity.
- After the first successful connection on `1.0.0`, moving the same counter to a different USB path should not require reconfiguration.
