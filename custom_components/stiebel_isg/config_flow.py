"""Config flow for STIEBEL ISG."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .api import StiebelIsgClient, StiebelIsgError
from .const import (
    CONF_OFFSET,
    CONF_UNIT_ID,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_UNIT_ID,
    DOMAIN,
)


class StiebelIsgConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_UNIT_ID]}"
            )
            self._abort_if_unique_id_configured()
            client = StiebelIsgClient(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_UNIT_ID],
                DEFAULT_TIMEOUT,
            )
            try:
                offset = await client.detect_offset()
            except StiebelIsgError:
                errors["base"] = "cannot_connect"
            except (
                Exception
            ):  # Home Assistant config flows must not expose library errors.
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"STIEBEL ISG ({user_input[CONF_HOST]})",
                    data={**user_input, CONF_OFFSET: offset},
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=247)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
