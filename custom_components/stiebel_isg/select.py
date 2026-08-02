"""Select entities for explicitly writable STIEBEL ISG parameters."""

from typing import ClassVar

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import OPERATING_MODE_FROM_VALUE, OPERATING_MODE_TO_VALUE
from .coordinator import StiebelIsgCoordinator
from .entity import StiebelIsgEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: StiebelIsgCoordinator = entry.runtime_data
    async_add_entities(
        [StiebelOperatingModeSelect(coordinator, entry.entry_id, entry.data[CONF_HOST])]
    )


class StiebelOperatingModeSelect(StiebelIsgEntity, SelectEntity):
    """Select for the documented WPMsystem operating mode register 1501."""

    _attr_name = "Operating mode"
    _attr_translation_key = "operating_mode"
    _attr_options: ClassVar[list[str]] = list(OPERATING_MODE_TO_VALUE)
    _attr_icon = "mdi:heat-pump-outline"

    def __init__(self, coordinator, entry_id, host) -> None:
        super().__init__(coordinator, entry_id, host)
        self._attr_unique_id = f"{entry_id}_operating_mode"

    @property
    def available(self) -> bool:
        item = self.coordinator.data.get("operating_mode")
        return (
            super().available
            and item is not None
            and item.available
            and item.plausible
            and item.value in OPERATING_MODE_FROM_VALUE
        )

    @property
    def current_option(self) -> str | None:
        item = self.coordinator.data.get("operating_mode")
        if item is None or not item.available:
            return None
        return OPERATING_MODE_FROM_VALUE.get(item.value)

    async def async_select_option(self, option: str) -> None:
        if option not in OPERATING_MODE_TO_VALUE:
            raise ValueError(f"Unsupported operating mode: {option}")
        await self.coordinator.async_set_operating_mode(OPERATING_MODE_TO_VALUE[option])
