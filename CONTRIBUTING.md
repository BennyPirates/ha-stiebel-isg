# Contributing

Thanks for helping improve STIEBEL ISG for Home Assistant.

## Before opening an issue

- Remove private IP addresses, credentials, serial numbers, and personal data.
- State the heat pump, controller, gateway, and firmware versions.
- Attach only the relevant, anonymised diagnostic rows.
- For unknown registers, report the address, register type, raw value, and
  repeatability. Do not assign a meaning without official documentation.

## Safety boundary

The current integration is read-only. Contributions must not add Modbus write
calls, writable Home Assistant entities, or services that change equipment
state. A future write-capable phase requires a separate design and review.

## Development checks

```bash
python -m unittest discover -s tests -v
python -m compileall custom_components src
```

Keep pull requests focused and explain how the change was tested.
