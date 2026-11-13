"""Support for MCLH-09 numbers (settings)."""
import logging
from datetime import timedelta
from homeassistant.components.number import NumberEntity, NumberMode
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
    async_add_entities([MCLH09UpdateInterval(coordinator, address)])

# Убираем CoordinatorEntity
class MCLH09UpdateInterval(NumberEntity):
    """Representation of the update interval setting."""

    def __init__(self, coordinator: MCLH09Coordinator, address: str):
        self.coordinator = coordinator
        self._address = address
        self._attr_name = "Update Interval (hours)"
        self._attr_unique_id = f"{address}_update_interval"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 24
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:timer-outline"
        # Поле всегда доступно
        self._attr_available = True
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    @property
    def native_value(self) -> float:
        if self.coordinator.update_interval:
            return self.coordinator.update_interval.total_seconds() / 3600
        return 1

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.update_interval = timedelta(hours=value)
        self.async_write_ha_state()
        _LOGGER.info("Update interval changed to %s hours", value)
