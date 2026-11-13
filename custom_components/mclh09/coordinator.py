"""DataUpdateCoordinator for MCLH-09."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import List
from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components import bluetooth

from .const import (
    DOMAIN,
    CHARACTERISTIC_DATA_UUID,
    CHARACTERISTIC_BATTERY_UUID,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=1)

# Калибровочные таблицы
TEMP_IN = [1035, 909, 648, 424, 368, 273, 159, 0]
TEMP_OUT = [68.8, 49.8, 23.7, 6.4, 1.0, -5.5, -20.5, -41.0]

SOIL_IN = [1280, 1216, 1146, 1076, 1006, 936, 900]
SOIL_OUT = [100.0, 90.28, 70.28, 50.28, 30.28, 10.28, 0.0]

LUMI_IN = [1453, 764, 741, 706, 645, 545, 196, 117, 24, 17, 0]
LUMI_OUT = [26700.0, 20700.0, 15700.0, 11700.0, 7700.0, 4000.0, 1500.0, 444.0, 29.0, 17.0, 0.0]

def limit_value(value: float, min_value: float, max_value: float) -> float:
    return min(max(value, min_value), max_value)

def interpolate(value: float, input_array: List[float], output_array: List[float], limit: bool = False) -> float:
    if len(input_array) != len(output_array) or len(input_array) < 3:
        _LOGGER.error("Bad size of input/output arrays for interpolate()")
        return float("nan")
    
    i = 0
    while i < len(input_array) - 1 and value < input_array[i + 1]:
        i += 1
        
    result = (output_array[i] - output_array[i + 1]) * (value - input_array[i + 1]) / (input_array[i] - input_array[i + 1]) + output_array[i + 1]
    
    if limit:
        return limit_value(result, output_array[-1], output_array[0])
    return result


class MCLH09Coordinator(DataUpdateCoordinator):
    """Class to manage fetching MCLH-09 data."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        """Initialize."""
        self.address = address
        self.name = name
        self.last_success_time = None 
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{address}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from the device."""
        device = async_ble_device_from_address(self.hass, self.address, connectable=True)
        if not device:
            raise UpdateFailed(f"Device {self.address} not found")

        # Берем RSSI из рекламных данных (надежнее, чем device.rssi)
        service_info = bluetooth.async_last_service_info(self.hass, self.address)
        rssi_val = service_info.rssi if service_info else None
        if rssi_val is not None:
            _LOGGER.debug("RSSI from advert: %s", rssi_val)

        data = {}
        if rssi_val is not None:
            data["rssi"] = rssi_val

        try:
            # Добавлен таймаут, чтобы не вешать HA, если датчик не отвечает
            client = await establish_connection(
                BleakClient, device, self.name, max_attempts=3, timeout=30.0
            )
            
            try:
                # Читаем батарею
                try:
                    batt_data = await client.read_gatt_char(CHARACTERISTIC_BATTERY_UUID)
                    data["battery"] = batt_data[0]
                except Exception as e:
                    _LOGGER.error("Failed to read battery: %s", e)
                    data["battery"] = None

                # Читаем основные данные
                try:
                    raw_data = await client.read_gatt_char(CHARACTERISTIC_DATA_UUID)
                    
                    if len(raw_data) >= 8:
                        temp_raw = raw_data[0] | (raw_data[1] << 8)
                        humi_raw = raw_data[2] | (raw_data[3] << 8)
                        soil_raw = raw_data[4] | (raw_data[5] << 8)
                        lumi_raw = raw_data[6] | (raw_data[7] << 8)
                        
                        # Применяем калибровку!
                        data["temperature"] = interpolate(float(temp_raw), TEMP_IN, TEMP_OUT)
                        data["humidity"] = float(humi_raw) / 13.0
                        data["soil_moisture"] = interpolate(float(soil_raw), SOIL_IN, SOIL_OUT, True)
                        data["illuminance"] = interpolate(float(lumi_raw), LUMI_IN, LUMI_OUT)
                    else:
                        _LOGGER.warning("Received unexpected data length: %s", len(raw_data))
                except Exception as e:
                    _LOGGER.error("Failed to read data characteristic: %s", e)

            finally:
                await client.disconnect()

            # Сохраняем время успешного обновления
            from homeassistant.util import dt as dt_util
            self.last_success_time = dt_util.utcnow()

            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err
