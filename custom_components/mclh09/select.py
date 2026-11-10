"""Support for MCLH-09 alert select (writing commands)."""
import logging
import asyncio
from bleak import BleakClient
from bleak_retry_connector import establish_connection
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.bluetooth import async_ble_device_from_address

from .const import DOMAIN
from .coordinator import MCLH09Coordinator

_LOGGER = logging.getLogger(__name__)

# Коды команд и их понятные названия
ALERT_COMMANDS = {
    "Off": 0x00,
    "Calibrate Temp (Red)": 0x01,                  # Калибровка температуры (+24.6°C)
    "Calibrate Soil/Lux (Green)": 0x02,            # Калибровка влажности почвы и света
    "Factory Reset (Red+Green)": 0x03,             # Сброс на заводские значения
    "Soil to 0% (Green)": 0x04,                    # Постоянный 0% влажности
    "Soil to 100% (Green)": 0x05,                  # Постоянный 100% влажности
}

# Иконки для каждой опции (mdi:...)
ALERT_ICONS = {
    "Off": "mdi:power",
    "Calibrate Temp (Red)": "mdi:thermometer",
    "Calibrate Soil/Lux (Green)": "mdi:white-balance-sunny",
    "Factory Reset (Red+Green)": "mdi:restore",
    "Soil to 0% (Green)": "mdi:water-off",
    "Soil to 100% (Green)": "mdi:water",
}

# Список команд, которые должны сбрасываться на "Off" после выполнения
ONCE_COMMANDS = [
    "Calibrate Temp (Red)", 
    "Calibrate Soil/Lux (Green)", 
    "Factory Reset (Red+Green)",
    "Soil to 0% (Green)",
    "Soil to 100% (Green)"
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MCLH-09 select."""
    coordinator: MCLH09Coordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data["address"]
    async_add_entities([MCLH09AlertSelect(coordinator, address)])


class MCLH09AlertSelect(CoordinatorEntity, SelectEntity):
    """Representation of the alert select."""

    def __init__(self, coordinator: MCLH09Coordinator, address: str):
        """Initialize the select."""
        super().__init__(coordinator)
        self._address = address
        self._attr_name = "Alert Select"
        self._attr_unique_id = f"{address}_alert_select"
        self._attr_options = list(ALERT_COMMANDS.keys())
        self._attr_current_option = "Off"
        
        # Применяем иконки к опциям
        self._attr_options_icons = ALERT_ICONS
        self._attr_icon = "mdi:alarm-light"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    async def async_select_option(self, option: str) -> None:
        """Send the selected command to the device."""
        _LOGGER.warning("=== ALERT: Начинаю отправку команды: %s ===", option)
        
        device = async_ble_device_from_address(self.hass, self._address, connectable=True)
        if not device:
            _LOGGER.error("ALERT: Устройство не найдено!")
            return

        await asyncio.sleep(1)

        try:
            client = await establish_connection(BleakClient, device, self._address, max_attempts=3)
            try:
                target_handle = 16
                
                value = ALERT_COMMANDS[option]
                _LOGGER.warning("ALERT: Пытаюсь записать 0x%02X в handle=%s...", value, target_handle)
                
                await client.write_gatt_char(target_handle, bytes([value]), response=False)
                _LOGGER.warning("ALERT: Команда 0x%02X ОТПРАВЛЕНА УСПЕШНО!", value)
                
            finally:
                await client.disconnect()
                
            # Обновляем состояние селектора
            if option in ONCE_COMMANDS:
                self._attr_current_option = "Off"
            else:
                self._attr_current_option = option
            self.async_write_ha_state()
            
            # САМОЕ ВАЖНОЕ: Принудительно запрашиваем обновление данных у координатора
            _LOGGER.info("ALERT: Запрашиваю немедленное обновление данных...")
            await self.coordinator.async_request_refresh()
                
        except Exception as e:
            _LOGGER.error("ALERT: ОШИБКА ОТПРАВКИ: %s", e)