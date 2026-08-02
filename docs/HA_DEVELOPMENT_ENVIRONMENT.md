# Home Assistant development environment

Status date: 2026-08-02

## Local repository

- Python 3.13 virtual environment: `.venv`
- Runtime dependency lock: `requirements.txt`
- Development dependency lock: `requirements-dev.txt`
- Unit tests: Python `unittest`
- Formatter and linter: Ruff
- Static type checking: mypy (the standalone diagnostic probe)
- Home Assistant validation: hassfest and HACS GitHub Actions
- Durable agent safety and workflow rules: `AGENTS.md`

Bootstrap and validate:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/python -m unittest discover -s tests -v
```

The custom integration imports Home Assistant internals that are available in
the HA runtime. Full strict typing of that package will be added when a pinned
Home Assistant development/test environment is introduced. The independent
diagnostic program is already checked in strict mode.

## Community Home Assistant MCP

The HA-MCP custom component is connected to Codex through its local direct
access endpoint. The endpoint is stored only in the user's global Codex
configuration. Its secret path is a credential and must never be committed or
printed in logs.

Live versions at the time of this audit:

- HA-MCP custom component 1.3.0
- HA-MCP server 8.0.0 (current; no update available)
- Home Assistant Core 2026.7.4
- Home Assistant OS 18.2 on Home Assistant Green
- Supervisor 2026.07.5

The connection is operational. Read-only mode was **not enabled** during the
audit, so mutation-capable tools are exposed. The audit nevertheless invoked
only read operations. Enabling HA-MCP read-only mode is recommended for routine
inventory and analysis; temporarily enable writes only for an explicitly
approved implementation task.

### Runtime capability inventory

The server exposes 78 tools. The exact live catalogue is grouped below.

Read/query tools (32):

```text
ha_config_get_automation, ha_config_get_calendar_events,
ha_config_get_category, ha_config_get_dashboard, ha_config_get_label,
ha_config_get_scene, ha_config_get_script, ha_config_list_dashboard_resources,
ha_config_list_groups, ha_config_list_helpers, ha_eval_template, ha_get_addon,
ha_get_automation_traces, ha_get_blueprint, ha_get_camera_image, ha_get_device,
ha_get_entity, ha_get_entity_exposure, ha_get_hacs_info, ha_get_history,
ha_get_integration, ha_get_logs, ha_get_operation_status, ha_get_overview,
ha_get_skill_guide, ha_get_state, ha_get_system_health, ha_get_todo,
ha_get_zone, ha_list_floors_areas, ha_list_services, ha_search
```

Entity/device/service control tools (3):

```text
ha_bulk_control, ha_call_event, ha_call_service
```

Configuration mutation tools (31):

```text
ha_config_delete_dashboard, ha_config_delete_dashboard_resource,
ha_config_remove_automation, ha_config_remove_calendar_event,
ha_config_remove_category, ha_config_remove_group, ha_config_remove_label,
ha_config_remove_scene, ha_config_remove_script, ha_config_set_automation,
ha_config_set_calendar_event, ha_config_set_category, ha_config_set_dashboard,
ha_config_set_dashboard_resource, ha_config_set_group, ha_config_set_helper,
ha_config_set_label, ha_config_set_scene, ha_config_set_script,
ha_remove_area_or_floor, ha_remove_device, ha_remove_entity,
ha_remove_helpers_integrations, ha_remove_todo_item, ha_remove_zone,
ha_set_area_or_floor, ha_set_device, ha_set_entity, ha_set_integration,
ha_set_todo_item, ha_set_zone
```

System/package mutation tools (12):

```text
ha_import_blueprint, ha_manage_addon, ha_manage_backup,
ha_manage_energy_prefs, ha_manage_hacs, ha_manage_pipeline, ha_manage_radio,
ha_manage_theme, ha_manage_updates, ha_reload_core, ha_report_issue, ha_restart
```

File/YAML tooling is installed as a second HA integration, but no dedicated
file read/write tools appeared in this live Codex catalogue. Dashboards and
their storage configurations are available through the dashboard tools.

### Read-only system inventory

- 1,674 entities across 36 domains and 22 areas
- 210 devices
- 55 integration entries: 50 loaded, 3 ignored/not loaded, 1 setup error and
  1 retrying
- 55 automations: 45 enabled and 10 disabled
- 5 listed custom/storage dashboards; system health reports 6 dashboards,
  13 views and 17 dashboard resources in total
- 5 installed add-ons: Matter Server, AirSonos, File editor, Get HACS and
  OpenThread Border Router; 4 running, Get HACS stopped, no updates pending
- HACS 2.0.5 is running with 29 downloaded repositories
- HA configuration validation succeeds with no errors
- One active repair concerns reauthentication of the Roborock integration
- No `climate` entities currently exist; future STIEBEL climate controls will
  therefore introduce a new entity domain if implemented that way
- Relevant energy foundations already include Fronius, Forecast.Solar, Tibber,
  Electricity Maps and energy-related sensors/automations

Integration health exceptions observed: one Raspberry Pi power integration is
in setup error and Synology DSM is retrying. Three ignored discovery entries
are intentionally not loaded.

The secret endpoint, tokens, private addresses, entity states that reveal
personal data, and full logs must not be committed.
