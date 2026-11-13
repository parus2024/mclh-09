"""Support for MCLH-09 sensors."""
import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
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
        # Сенсор последнего обновления
        MCLH09LastUpdatedSensor(coordinator, address),
    ]
    async_add_entities(sensors)


class MCLH09Sensor(CoordinatorEntity, SensorEntity):
    """Representation of a MCLH-09 sensor."""

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

        # Привязываем к устройству, чтобы сенсоры группировались
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)


class MCLH09LastUpdatedSensor(CoordinatorEntity, SensorEntity):
    """Representation of the last update time."""

    def __init__(self, coordinator, address):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Last Updated"
        self._attr_unique_id = f"{address}_last_updated"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-check-outline"
        self._attr_update_period = timedelta(seconds=60)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "name": f"MCLH-09 {address[-5:]}",
            "manufacturer": "MCLH",
            "model": "MCLH-09",
        }

    @property
    def native_value(self):
        """Return the last successful update timestamp."""
        return self.coordinator.last_success_time
