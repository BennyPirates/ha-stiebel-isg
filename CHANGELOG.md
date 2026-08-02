# Changelog

## 0.1.0 – 2026-08-02

- Add HACS-installable Home Assistant integration with UI config flow.
- Detect document-to-PDU address offset automatically.
- Expose selected WPMsystem values as sensors and binary sensors.
- Treat unavailable `0x8000` registers dynamically, including cooling values.
- Represent SG Ready raw value 0 as disabled.
- Poll locally every 30 seconds with conservative request pacing.
- Keep the complete runtime strictly read-only with Modbus FC03 and FC04.
- Include the standalone diagnostic probe, JSON/CSV export, and tests.
