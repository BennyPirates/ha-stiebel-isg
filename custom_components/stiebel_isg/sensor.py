"""Read-only sensors for STIEBEL ISG."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import StiebelIsgCoordinator
from .entity import StiebelIsgEntity
from .registers import REGISTERS

SG_READY_STATES = {0: "Disabled", 1: "Blocked", 2: "Normal", 3: "Boost", 4: "Forced"}
WRITABLE_ENTITY_KEYS = {
    "operating_mode",
    "hc1_comfort_temperature",
    "hc1_eco_temperature",
    "hc1_heating_curve",
    "dhw_comfort_temperature",
    "dhw_eco_temperature",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: StiebelIsgCoordinator = entry.runtime_data
    async_add_entities(
        StiebelIsgSensor(coordinator, entry.entry_id, entry.data[CONF_HOST], register)
        for register in REGISTERS
        if register.key not in WRITABLE_ENTITY_KEYS | {"operating_status"}
    )


class StiebelIsgSensor(StiebelIsgEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, host, register) -> None:
        super().__init__(coordinator, entry_id, host)
        self.register = register
        self._attr_unique_id = f"{entry_id}_{register.key}"
        self._attr_name = register.name
        self._attr_native_unit_of_measurement = register.unit
        self._attr_device_class = register.device_class
        self._attr_state_class = register.state_class

    @property
    def available(self) -> bool:
        item = self.coordinator.data.get(self.register.key)
        return (
            super().available and item is not None and item.available and item.plausible
        )

    @property
    def native_value(self):
        item = self.coordinator.data.get(self.register.key)
        if item is None or not item.available:
            return None
        if self.register.key == "sg_ready_state":
            return SG_READY_STATES.get(item.value, f"Unknown ({item.value})")
        return item.value

    @property
    def extra_state_attributes(self):
        item = self.coordinator.data.get(self.register.key)
        return {
            "register": self.register.address,
            "register_type": self.register.kind,
            "raw_value": item.raw if item else None,
            "plausible": item.plausible if item else False,
        }
