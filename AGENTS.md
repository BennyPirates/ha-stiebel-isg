# Development rules

This repository contains a Home Assistant custom integration and a separate
diagnostic probe for STIEBEL ELTRON WPMsystem devices through ISG Connect.

## Safety boundary

- Modbus access is read-only. Only FC03 and FC04 are permitted.
- Never add or invoke FC05, FC06, FC15, FC16, FC22, FC23, or another write
  operation without the user's explicit approval for that specific change.
- Do not change Home Assistant, its entities, automations, dashboards, add-ons,
  configuration, or files unless the user explicitly requests that change.
- Inventory and diagnosis of Home Assistant must use the configured Community
  Home Assistant MCP. Direct HA filesystem or REST access is not a fallback.
- Announce integration reloads and Home Assistant restarts before invoking them.
- Ask before destructive changes or changes that affect devices outside this
  repository.
- Never commit local IP addresses, MCP secret URLs, access tokens, probe result
  data, or vendor PDFs.

## Workflow

- Keep changes small and reviewable; preserve unrelated user changes.
- Add or update tests for behavior changes.
- Before committing, run `ruff format --check .`, `ruff check .`, `mypy`, and
  `python -m unittest discover -s tests -v`.
- Use meaningful commits and do not push unless requested.
- Prefer MCP tools for Home Assistant operations. Use repository file edits for
  source code, tests, documentation, and CI configuration.
