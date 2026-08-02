"""Read-only status binary sensors for STIEBEL ISG."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import StiebelIsgCoordinator
from .entity import StiebelIsgEntity
from .registers import STATUS_BITS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: StiebelIsgCoordinator = entry.runtime_data
    async_add_entities(
        StiebelStatusSensor(
            coordinator, entry.entry_id, entry.data[CONF_HOST], key, bit, name
        )
        for key, (bit, name) in STATUS_BITS.items()
    )


class StiebelStatusSensor(StiebelIsgEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry_id, host, key, bit, name) -> None:
        super().__init__(coordinator, entry_id, host)
        self._bit = bit
        self._attr_unique_id = f"{entry_id}_status_{key}"
        self._attr_name = name

    @property
    def available(self) -> bool:
        item = self.coordinator.data.get("operating_status")
        return super().available and item is not None and item.available

    @property
    def is_on(self) -> bool | None:
        item = self.coordinator.data.get("operating_status")
        return (
            None
            if item is None or item.value is None
            else bool(int(item.value) & (1 << self._bit))
        )
