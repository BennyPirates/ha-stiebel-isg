"""Number entities for explicitly writable STIEBEL ISG parameters."""

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import StiebelIsgCoordinator
from .entity import StiebelIsgEntity


@dataclass(frozen=True, slots=True)
class NumberDescription:
    key: str
    name: str
    minimum: float
    maximum: float
    step: float
    icon: str
    unit: str | None = None
    device_class: NumberDeviceClass | None = None


NUMBER_DESCRIPTIONS = (
    NumberDescription(
        "hc1_comfort_temperature",
        "HC1 comfort temperature",
        5,
        30,
        0.1,
        "mdi:home-thermometer",
        UnitOfTemperature.CELSIUS,
        NumberDeviceClass.TEMPERATURE,
    ),
    NumberDescription(
        "hc1_eco_temperature",
        "HC1 Eco temperature",
        5,
        30,
        0.1,
        "mdi:leaf-thermometer",
        UnitOfTemperature.CELSIUS,
        NumberDeviceClass.TEMPERATURE,
    ),
    NumberDescription(
        "hc1_heating_curve", "HC1 heating curve", 0, 3, 0.01, "mdi:chart-bell-curve"
    ),
    NumberDescription(
        "dhw_comfort_temperature",
        "DHW comfort temperature",
        10,
        60,
        0.5,
        "mdi:water-thermometer",
        UnitOfTemperature.CELSIUS,
        NumberDeviceClass.TEMPERATURE,
    ),
    NumberDescription(
        "dhw_eco_temperature",
        "DHW Eco temperature",
        10,
        60,
        0.5,
        "mdi:water-thermometer-outline",
        UnitOfTemperature.CELSIUS,
        NumberDeviceClass.TEMPERATURE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: StiebelIsgCoordinator = entry.runtime_data
    async_add_entities(
        StiebelWritableNumber(
            coordinator, entry.entry_id, entry.data[CONF_HOST], description
        )
        for description in NUMBER_DESCRIPTIONS
    )


class StiebelWritableNumber(StiebelIsgEntity, NumberEntity):
    """One explicitly allow-listed WPMsystem numeric setting."""

    def __init__(self, coordinator, entry_id, host, description) -> None:
        super().__init__(coordinator, entry_id, host)
        self._description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_translation_key = description.key
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.unit
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_native_step = description.step

    @property
    def available(self) -> bool:
        item = self.coordinator.data.get(self._description.key)
        return (
            super().available and item is not None and item.available and item.plausible
        )

    @property
    def native_value(self) -> float | None:
        item = self.coordinator.data.get(self._description.key)
        if item is None or item.value is None:
            return None
        return float(item.value)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_number_parameter(self._description.key, value)
