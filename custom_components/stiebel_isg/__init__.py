"""STIEBEL ISG read-only integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .api import StiebelIsgClient
from .const import CONF_OFFSET, CONF_UNIT_ID, DEFAULT_TIMEOUT, PLATFORMS
from .coordinator import StiebelIsgCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = StiebelIsgClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_UNIT_ID],
        DEFAULT_TIMEOUT,
    )
    coordinator = StiebelIsgCoordinator(hass, client, entry.data[CONF_OFFSET])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
