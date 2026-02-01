# Rad Pro USB for Home Assistant

Custom Home Assistant integration that reads a Rad Pro device over USB serial and exposes sensor entities similar to the MQTT payloads used by the `radpro-wifi-bridge` project.

## Features
- Polls a Rad Pro device connected via USB serial.
- Creates sensors for each configured command (default: `tubeRate`, `tubePulseCount`, `doseRate`).
- Optional derived CPS/CPM sensors based on `tubePulseCount`.
- Config flow with options to change commands and polling interval.

## Installation

### HACS (custom repository)
1. In HACS, add this repository as a custom integration.
2. Install **Rad Pro USB**.
3. Restart Home Assistant.
4. Add the integration from **Settings → Devices & Services**.

### Manual
1. Copy `custom_components/radpro_usb` into your Home Assistant `config/custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & Services**.

## Configuration

From the UI config flow you will be asked for:
- Serial port (example: `/dev/serial/by-id/...` or `/dev/ttyUSB0`).
- Baud rate (default `115200`).
- Serial timeout in seconds (default `1.0`).
- Polling interval in seconds (default `5`).
- Commands (comma-separated).
- Whether to enable derived CPS/CPM sensors.

### Commands
The default command list is:
```
tubeRate,tubePulseCount,doseRate
```
If your device firmware does not support a command, remove it from the list in the integration options.

## Sensors
- **Tube Rate** (`tubeRate`) - counts per minute (CPM).
- **Tube Pulse Count** (`tubePulseCount`) - cumulative pulses.
- **Dose Rate** (`doseRate`) - uSv/h when supported by firmware.
- **Derived CPS/CPM** (optional) - calculated from pulse count deltas.

## Troubleshooting
- Make sure Home Assistant can access the serial device (use `/dev/serial/by-id` when possible).
- Ensure no other process is using the serial device.
- Turn on debug logging for `custom_components.radpro_usb` to inspect raw responses.

## Logging
Add to `configuration.yaml`:
```
logger:
  default: info
  logs:
    custom_components.radpro_usb: debug
```

## Disclaimer
This integration relies on the Rad Pro serial command interface. If your device uses different commands or baud rate, adjust the integration options accordingly.
