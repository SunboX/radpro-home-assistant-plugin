# Troubleshooting

## No data
- Verify the serial port path and permissions.
- Make sure the Rad Pro device is not opened by another application.
- Lower the polling interval if your device is slow to respond.
- If you upgraded from a pre-`1.0.0` version, connect each existing counter once on its previously configured port so the entry can migrate to `deviceId`-based identity.
- After migration, the integration should automatically follow that same physical counter when its USB path changes.

## Debug logging
Add to `configuration.yaml`:
```
logger:
  default: info
  logs:
    custom_components.radpro_usb: debug
```
Restart Home Assistant and inspect the logs for raw responses.
