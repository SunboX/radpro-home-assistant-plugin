<!--
SPDX-FileCopyrightText: 2026 André Fiedler

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Rad Pro USB

Home Assistant custom integration for reading Rad Pro devices over USB serial.

## Features

- Polls a Rad Pro device connected over USB serial.
- Supports multiple attached counters as separate Home Assistant entries.
- Tracks each entry by the physical counter `deviceId` and automatically follows USB path changes after migration.
- Exposes Rad Pro measurements as Home Assistant sensor and binary sensor entities.
- Includes a config flow with configurable polling and optional derived CPS/CPM sensors.

## Installation

While this repository is pending inclusion in the default HACS store, install it as a custom integration:

1. Open HACS.
2. Open the top-right menu and select **Custom repositories**.
3. Add `https://github.com/SunboX/radpro-home-assistant-plugin` as an **Integration** repository.
4. Install **Rad Pro USB**.
5. Restart Home Assistant.

## Configuration

After installation, go to **Settings -> Devices & Services -> Add Integration** and search for **Rad Pro USB**.

You will be asked for:

- The serial port path for the connected Rad Pro device.
- Baud rate and serial timeout.
- Polling interval.
- Whether derived CPS/CPM sensors should be created.

Each added entry represents one physical counter.

## License

The software source code is licensed under GNU Affero General Public License v3.0 or later (`AGPL-3.0-or-later`).

Closed-source, proprietary, or otherwise AGPL-incompatible use requires a separate commercial/proprietary license from the copyright holder.
