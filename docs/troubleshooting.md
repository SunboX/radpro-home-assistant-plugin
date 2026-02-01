# Troubleshooting

## No data
- Verify the serial port path and permissions.
- Make sure the Rad Pro device is not opened by another application.
- Lower the polling interval if your device is slow to respond.

## Debug logging
Add to `configuration.yaml`:
```
logger:
  default: info
  logs:
    custom_components.radpro_usb: debug
```
Restart Home Assistant and inspect the logs for raw responses.
