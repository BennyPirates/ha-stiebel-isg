"""Shared STIEBEL ISG entity."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StiebelIsgCoordinator


class StiebelIsgEntity(CoordinatorEntity[StiebelIsgCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: StiebelIsgCoordinator, entry_id: str, host: str
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="STIEBEL ISG",
            manufacturer="STIEBEL ELTRON",
            model="ISG Connect",
            configuration_url=f"http://{host}",
        )
