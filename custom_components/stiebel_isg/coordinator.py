"""Data coordinator for STIEBEL ISG."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StiebelIsgClient, StiebelIsgError, Value
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class StiebelIsgCoordinator(DataUpdateCoordinator[dict[str, Value]]):
    def __init__(self, hass: HomeAssistant, client: StiebelIsgClient, offset: int) -> None:
        super().__init__(hass, logger=_LOGGER, name=DOMAIN,
                         update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.client, self.offset = client, offset

    async def _async_update_data(self) -> dict[str, Value]:
        try:
            return await self.client.read_all(self.offset)
        except StiebelIsgError as error:
            raise UpdateFailed(str(error)) from error
