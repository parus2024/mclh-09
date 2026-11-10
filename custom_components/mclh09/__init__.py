"""The MCLH-09 Plant Sensor integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MCLH09Coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button", "number", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MCLH-09 from a config entry."""
    address = entry.data["address"]
    name = entry.title
    
    _LOGGER.info("Setting up MCLH-09 integration for %s (%s)", name, address)
    
    coordinator = MCLH09Coordinator(hass, address, name)
    
    # Выполняем первый опрос
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok