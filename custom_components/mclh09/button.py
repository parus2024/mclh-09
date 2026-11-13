"""Support for MCLH-09 buttons."""
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MCLH09Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MCLH09Coordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data["address"]
    async_add_entities([MCLH09RefreshButton(coordinator, address)])


class MCLH09RefreshButton(ButtonEntity):
    """Representation of a manual refresh button."""

    def __init__(self, coordinator: MCLH09Coordinator, address: str):
        self.coordinator = coordinator
        self._address = address
        self._attr_name = "Refresh Data"
        self._attr_unique_id = f"{address}_refresh"
        self._attr_icon = "mdi:refresh"
        # Кнопка всегда доступна
        self._attr_available = True
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    async def async_press(self) -> None:
        _LOGGER.info("Manual update requested for %s", self._address)
        await self.coordinator.async_refresh()
