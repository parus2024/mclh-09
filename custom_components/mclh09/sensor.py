"""Support for MCLH-09 sensors."""
import logging
from datetime import timedelta
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    RestoreSensor,
)
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
    """Set up MCLH-09 sensors based on a config entry."""
    coordinator: MCLH09Coordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data["address"]

    sensors = [
        MCLH09Sensor(coordinator, address, "temperature", "Temperature", "°C", SensorDeviceClass.TEMPERATURE, 1),
        MCLH09Sensor(coordinator, address, "humidity", "Humidity", "%", SensorDeviceClass.HUMIDITY, 0),
        MCLH09Sensor(coordinator, address, "soil_moisture", "Soil Moisture", "%", SensorDeviceClass.MOISTURE, 0),
        MCLH09Sensor(coordinator, address, "illuminance", "Illuminance", "lx", SensorDeviceClass.ILLUMINANCE, 0),
        MCLH09Sensor(coordinator, address, "battery", "Battery", "%", SensorDeviceClass.BATTERY, 0),
        MCLH09Sensor(coordinator, address, "rssi", "RSSI", "dBm", SensorDeviceClass.SIGNAL_STRENGTH, 0),
        MCLH09LastUpdatedSensor(coordinator, address),
    ]
    async_add_entities(sensors)


class MCLH09Sensor(CoordinatorEntity, RestoreSensor):
    """Representation of a MCLH-09 sensor with state restoration."""

    def __init__(self, coordinator, address, key, name, unit, device_class, decimals):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = f"{address}_{key}"
        self._attr_suggested_display_precision = decimals
        self._attr_state_class = SensorStateClass.MEASUREMENT

        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    async def async_added_to_hass(self) -> None:
        """Restore state when Home Assistant starts."""
        await super().async_added_to_hass()
        
        # Восстанавливаем последнее состояние
        last_sensor_data = await self.async_get_last_sensor_data()
        if last_sensor_data is not None:
            self._attr_native_value = last_sensor_data.native_value
            _LOGGER.debug("Restored state for %s: %s", self.name, self._attr_native_value)
        
        # Подписываемся на обновления координатора
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        # Принудительно обновляем состояние при старте (чтобы показать восстановленное)
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data is not None and self._key in self.coordinator.data:
            self._attr_native_value = self.coordinator.data.get(self._key)
        # Если данных нет, мы не трогаем _attr_native_value, 
        # и он остается тем, что был восстановлен из кэша
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._attr_native_value


class MCLH09LastUpdatedSensor(CoordinatorEntity, RestoreSensor):
    """Representation of the last update time with restoration."""

    def __init__(self, coordinator, address):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Last Updated"
        self._attr_unique_id = f"{address}_last_updated"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-check-outline"
        # Обновляем отображение сенсора раз в минуту, чтобы не грузить систему
        self._attr_update_period = timedelta(seconds=60)
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    async def async_added_to_hass(self) -> None:
        """Restore state when Home Assistant starts."""
        await super().async_added_to_hass()
        
        # Восстанавливаем время последнего обновления
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in ("unknown", "unavailable"):
            from homeassistant.util import dt as dt_util
            restored_time = dt_util.parse_datetime(last_state.state)
            if restored_time is not None:
                self._attr_native_value = restored_time
                _LOGGER.debug("Restored time for %s: %s", self.name, self._attr_native_value)

        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.last_success_time is not None:
            self._attr_native_value = self.coordinator.last_success_time
        # Если время не обновилось, оставляем восстановленное значение
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the last successful update timestamp."""
        return self._attr_native_value
