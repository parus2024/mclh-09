"""Support for MCLH-09 buttons."""
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MCLH09Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MCLH-09 buttons."""
    coordinator: MCLH09Coordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data["address"]

    async_add_entities([MCLH09RefreshButton(coordinator, address)])


class MCLH09RefreshButton(CoordinatorEntity, ButtonEntity):
    """Representation of a manual refresh button."""

    def __init__(self, coordinator: MCLH09Coordinator, address: str):
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Обновить данные"
        self._attr_unique_id = f"{address}_refresh"
        self._attr_icon = "mdi:refresh"
        
        # Привязка к устройству
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Manual update requested")
        await self.coordinator.async_request_refresh()