"""Data coordinator for STIEBEL ISG."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StiebelIsgClient, StiebelIsgError, Value
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class StiebelIsgCoordinator(DataUpdateCoordinator[dict[str, Value]]):
    def __init__(
        self, hass: HomeAssistant, client: StiebelIsgClient, offset: int
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client, self.offset = client, offset

    async def _async_update_data(self) -> dict[str, Value]:
        try:
            return await self.client.read_all(self.offset)
        except StiebelIsgError as error:
            raise UpdateFailed(str(error)) from error

    async def async_set_operating_mode(self, mode: int) -> None:
        """Set the operating mode and immediately refresh coordinator data."""
        await self.client.set_operating_mode(mode, self.offset)
        await self.async_request_refresh()

    async def async_set_number_parameter(self, register_key: str, value: float) -> None:
        """Write one allow-listed numeric parameter and refresh state."""
        await self.client.set_number_parameter(register_key, value, self.offset)
        await self.async_request_refresh()
