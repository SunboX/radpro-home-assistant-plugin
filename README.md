<!--
SPDX-FileCopyrightText: 2026 André Fiedler

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Rad Pro USB for Home Assistant

Custom Home Assistant integration that reads a Rad Pro device over USB serial and exposes sensor entities similar to the MQTT payloads used by the `radpro-wifi-bridge` project.

This project builds on the excellent open-source Rad Pro firmware from https://github.com/Gissio/radpro.

## Features
- Polls a Rad Pro device connected via USB serial.
- Supports multiple attached Rad Pro counters as separate Home Assistant entries.
- Tracks each configured counter by `deviceId`, so replugging to another USB path does not require reconfiguration after migration.
- Creates sensors for each configured command (default: `tubeRate`, `tubePulseCount`, `doseRate`).
- Optional derived CPS/CPM sensors based on `tubePulseCount`.
- Config flow with polling interval and derived sensor toggle.

## Installation

### HACS
If this repository is already available in the default HACS store, search for **Rad Pro USB** in HACS and install it directly.

If the default-store inclusion is still pending, add it as a custom integration first:
1. In HACS, open the top-right menu and select **Custom repositories**.
2. Add `https://github.com/SunboX/radpro-home-assistant-plugin` as an **Integration** repository.
3. Install **Rad Pro USB**.
4. Restart Home Assistant.
5. Add the integration from **Settings → Devices & Services**.

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
- Whether to enable derived CPS/CPM sensors.

Each config entry represents one physical Rad Pro counter. Starting with `1.0.0`, the integration stores the device's `deviceId` and automatically rebinds the entry if that same counter appears on a different USB path later.

Existing installs are migrated automatically on the first successful connection after upgrading to `1.0.0`.

## Sensors
- **Power** (`devicePower`) - on/off status.
- **Battery Voltage** (`deviceBatteryVoltage`) - volts.
- **Battery** (`deviceBatteryPercent`) - percentage.
- **Tube Rate** (`tubeRate`) - counts per minute (CPM).
- **Tube Pulse Count** (`tubePulseCount`) - cumulative pulses.
- **Dose Rate** (`tubeDoseRate`) - µSv/h (computed from tube rate + sensitivity).
- **Tube Sensitivity** (`tubeSensitivity`) - cpm/µSv/h.
- **Tube Dead Time** (`tubeDeadTime`) - seconds.
- **Tube Dead Time Compensation** (`tubeDeadTimeCompensation`) - seconds.
- **Tube HV Frequency** (`tubeHvFrequency`) - Hz.
- **Tube HV Duty Cycle** (`tubeHvDutyCycle`) - ratio.
- **Device info** (`deviceId`, `deviceModel`, `deviceFirmware`, `deviceLocale`, `deviceTime`, `deviceTimeZone`) - diagnostics.
- **Derived CPS/CPM** (optional) - calculated from pulse count deltas.

## Troubleshooting
- Make sure Home Assistant can access the serial device (use `/dev/serial/by-id` when possible).
- Ensure no other process is using the serial device.
- If an upgraded entry does not follow a moved counter yet, reconnect the original device once so `1.0.0` can migrate it from port-based identity to `deviceId`.
- Turn on debug logging for `custom_components.radpro_usb` to inspect raw responses.
- Report issues at https://github.com/SunboX/radpro-home-assistant-plugin/issues.

## Logging
Add to `configuration.yaml`:
```
logger:
  default: info
  logs:
    custom_components.radpro_usb: debug
```

## License

This project is available under two licensing options:

### 1. Open-source license

GNU Affero General Public License v3.0 or later (`AGPL-3.0-or-later`).

You may use, modify, and distribute the software source code under the AGPL. If you modify the software and make it available to users over a network, the AGPL requires that those users can access the corresponding source code of the modified version.

### 2. Commercial/proprietary license

For use in closed-source, proprietary, or otherwise AGPL-incompatible products, a separate commercial/proprietary license is required.

Commercial licensing contact: https://github.com/SunboX

### Documentation and media

Documentation, images, and other non-code media are licensed under Creative Commons Attribution-ShareAlike 4.0 (`CC-BY-SA-4.0`) unless otherwise marked.

### Attribution / notices

Copyright (C) 2026 André Fiedler.

Copyright, license, attribution, and source-origin notices must be preserved as required by the applicable license and the notice files in this repository.

See [LICENSE.md](LICENSE.md), [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md), [NOTICE.md](NOTICE.md), and the machine-readable license texts in [LICENSES/](LICENSES/).

## Disclaimer
This integration relies on the Rad Pro serial command interface. If your device uses a different baud rate, adjust the integration options accordingly.
