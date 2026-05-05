<!--
SPDX-FileCopyrightText: 2026 André Fiedler

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Device Model Naming Design

## Summary

Change the Home Assistant config entry and device display name from the fixed `Rad Pro (<deviceId>)` format to `<deviceModel> (<deviceId>)` when the probed device reports a model. If the device does not report a model, keep the existing `Rad Pro (<deviceId>)` fallback.

## Goals

- Show a meaningful device name such as `Bosean FS-5000 (0e0036001451353137363534)` in Home Assistant.
- Preserve `deviceId` as the stable identity used for unique IDs and USB rebinding.
- Apply the same naming behavior to newly added entries and to existing entries when they are refreshed during setup.

## Non-Goals

- Do not change entity IDs, unique IDs, or the stored physical identity model.
- Do not add a separate persisted display-name field.
- Do not change the manufacturer or model metadata exposed through `DeviceInfo` beyond the name already derived from the entry title.

## Proposed Design

### Title Construction

Extend the shared title builder so it accepts:

- `device_id`: required stable physical identifier
- `model`: optional probed device model

The helper will return:

- `<model> (<deviceId>)` when `model` is a non-empty string after trimming
- `Rad Pro (<deviceId>)` when `model` is missing or empty

This keeps naming logic centralized and avoids duplicating display rules across config flow and setup migration paths.

### Entry Creation And Migration

Use the shared title builder in both places that currently create or update the entry title:

- config flow entry creation after probing the selected device
- setup-time identity refresh when rebinding or migrating an existing entry

Because `RadProDeviceIdentity` already carries `model`, no new storage field is required.

### Entity Device Naming

Sensor and binary sensor entities already use `entry.title` as `DeviceInfo.name`. That behavior should remain unchanged so the Home Assistant device list reflects the new naming automatically.

## Data Flow

1. Probe `GET deviceId`.
2. Parse `deviceModel` and `deviceId`.
3. Build the entry title from `deviceModel` plus `deviceId`, with `Rad Pro` fallback.
4. Persist the updated title while continuing to store `deviceId` as the stable identity.
5. Reuse `entry.title` as the device name for exposed entities.

## Error Handling

- If probing fails, keep the existing connection error behavior.
- If the response includes no usable `deviceModel`, fall back to `Rad Pro (<deviceId>)`.
- If an existing entry is refreshed and the resolved title already matches, avoid unnecessary entry writes as today.

## Testing

Add or update unit tests to cover:

- title builder returns `<model> (<deviceId>)` when a model is present
- title builder falls back to `Rad Pro (<deviceId>)` when the model is missing
- entry update description changes the stored title to the model-based name when a resolved identity includes a model
- entry update description still returns `None` when the entry already matches the resolved identity and title
