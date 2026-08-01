
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from custom_components.pure_energy_prices import PureEnergyData

from .const import (
    BASE_URL,
    CONF_ELEMENT_ID,
    CONF_DOUBLE_METER,
    CONF_SOLAR_PANELS,
    CONF_BUSINESS,
    CONF_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class PureEnergyCoordinator(DataUpdateCoordinator[PureEnergyData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name="Pure Energie Prices",
            update_interval=timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL, 3600)),
        )
        self.data = PureEnergyData([])

    async def _async_update_data(self) -> PureEnergyData:
        p = self.entry.data
        url = (
            f"{BASE_URL}"
            f"?double_meter={'true' if p.get(CONF_DOUBLE_METER, True) else 'false'}"
            f"&solar_panels={'true' if p.get(CONF_SOLAR_PANELS, True) else 'false'}"
            f"&commodity=electricity"
            f"&current=null"
            f"&business={'true' if p.get(CONF_BUSINESS, False) else 'false'}"
            f"&element_id={p.get(CONF_ELEMENT_ID)}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch Pure Energie prices: {e}") from e

        prices = payload.get("prices", []) or []
        return PureEnergyData(prices)