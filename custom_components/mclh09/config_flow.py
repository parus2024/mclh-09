"""Config flow for MCLH-09 integration."""
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
)
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MCLH09ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MCLH-09."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        
        # 1. ЭТА СТРОКА ДЕЛАЕТ MAC В КАРТОЧКЕ "ОБНАРУЖЕНО"
        self.context["title_placeholders"] = {
            "name": f"{discovery_info.name} ({discovery_info.address})"
        }
        
        self._discovery_info = discovery_info
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm setup."""
        if user_input is None:
            return self.async_show_form(
                step_id="confirm",
                description_placeholders={
                  "name": self._discovery_info.name,
                  "address": self._discovery_info.address,
                },
            )

        # 2. Здесь имя сохраняется уже в саму запись интеграции после добавления
        return self.async_create_entry(
            title=f"{self._discovery_info.name} ({self._discovery_info.address})",
            data={"address": self._discovery_info.address},
        )