# Configuration

Configuration is done through the UI.

## Required
- **Serial port**: The Rad Pro USB device path (recommended: `/dev/serial/by-id/...`).

## Optional
- **Baud rate**: Default `115200`.
- **Serial timeout**: Default `1.0` seconds.
- **Polling interval**: Default `5` seconds.
- **Commands**: Comma-separated list of Rad Pro commands to poll.
- **Derived sensors**: Enable CPS/CPM calculated from `tubePulseCount`.

## Command list
Default:
```
tubeRate,tubePulseCount,doseRate
```
If a command is unsupported by your firmware, remove it from the list in the integration options.
