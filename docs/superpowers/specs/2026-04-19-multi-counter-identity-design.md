# Rad Pro Multi-Counter Identity Design

## Summary

Each Home Assistant config entry will represent one physical Rad Pro counter, identified by the device's `deviceId`, not by the current USB serial path.

## Goals

- Allow multiple attached Rad Pro counters to coexist cleanly.
- Make each config entry follow the same physical counter when the USB path changes.
- Migrate existing port-based entries to device-ID-based identity automatically.
- Preserve existing entity registry stability where possible.

## Non-Goals

- One config entry managing multiple counters.
- Background global device manager infrastructure.
- Automatic creation of entries for newly attached counters.

## Approach

### Canonical identity

- Store `device_id` in config entry data.
- Set the config entry unique ID to `deviceId`.
- Keep `port` as mutable transport state, not canonical identity.

### New entries

- During config flow, probe the selected serial port.
- Read and parse `deviceId`.
- Abort if that physical counter is already configured.
- Create the entry with a stable title derived from `deviceId`.

### Existing entry migration

- During setup, if the entry does not yet have `device_id`, probe the configured port.
- On success, update entry data, title, and unique ID in place.
- The entry ID remains unchanged so entity unique IDs can stay stable.

### Port rebinding

- Setup first tries the saved port.
- If the saved port is missing, unreadable, or reports a different `deviceId`, scan detected Rad Pro ports.
- Probe each detected port until the saved `device_id` is found.
- Update the config entry with the new port transparently.
- If no matching counter is attached, setup fails cleanly and the entry remains tied to that physical counter for a later reconnect.

### Entity and device registry behavior

- Keep entity unique IDs based on `entry_id` to avoid entity churn for migrated installs.
- Switch `DeviceInfo.identifiers` from `(DOMAIN, entry_id)` to `(DOMAIN, device_id)` so Home Assistant models the physical counter as the device.
- Include `device_id` in extra state attributes for easier diagnosis.

## Files In Scope

- `custom_components/radpro_usb/config_flow.py`
- `custom_components/radpro_usb/__init__.py`
- `custom_components/radpro_usb/const.py`
- `custom_components/radpro_usb/sensor.py`
- `custom_components/radpro_usb/binary_sensor.py`
- `custom_components/radpro_usb/manifest.json`
- `README.md`
- `docs/configuration.md`
- `docs/installation.md`
- `docs/troubleshooting.md`
- `info.md`
- `tests/test_config_flow_helpers.py`
- `tests/test_coordinator_helpers.py`
- New setup/identity tests as needed

## Risks

- Config-entry mutation during setup must be done carefully to avoid reload loops.
- Serial probing during config/setup must close temporary clients reliably.
- Migration must not accidentally bind an entry to the wrong counter when two devices are attached.

## Validation

- Unit tests for identity parsing and config/setup helpers.
- Regression test for migration from port-based entries.
- Regression test for rebinding when the saved port changes.
- Existing suite must continue to pass.
