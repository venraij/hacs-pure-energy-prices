from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)
from homeassistant.components.sensor import SensorEntity

from .const import (
    DOMAIN,
    BASE_URL,
    CONF_ELEMENT_ID,
    CONF_DOUBLE_METER,
    CONF_SOLAR_PANELS,
    CONF_BUSINESS,
    CONF_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

@dataclass
class PureEnergyData:
    prices: list[dict[str, Any]]

class PureEnergyCoordinator(DataUpdateCoordinator[PureEnergyData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name="Pure Energie Prices",
            update_interval=timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL, 3600)),
        )
        self.data = PureEnergyData(prices=[])

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
                async with session.get(url, timeout=30) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch Pure Energie prices: {e}") from e

        prices = payload.get("prices", []) or []
        return PureEnergyData(prices=prices)

class PureEnergyPricesSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity):
    _attr_name = "Pure Energie prices"
    _attr_unique_id = "pure_energy_prices"
    _attr_unit_of_measurement = "€/kWh"
    _attr_native_value = None

    @property
    def native_value(self):
        return None

    @property
    def extra_state_attributes(self):
        return {"prices": self.coordinator.data.prices}

class PureEnergyCurrentAllInSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity):
    _attr_name = "Pure Energie current all-in price"
    _attr_unique_id = "pure_energy_current_all_in_price"
    _attr_unit_of_measurement = "€/kWh"

    @property
    def native_value(self):
        prices = self.coordinator.data.prices or []
        current = next(
            (r for r in prices if r.get("date", {}).get("current") is True),
            None,
        )
        if not current:
            return None
        return float(current.get("price", 0))

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = PureEnergyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            PureEnergyPricesSensor(coordinator),
            PureEnergyCurrentAllInSensor(coordinator),
        ]
    )

    # Keep a ref if you want debugging later
    @callback
    def _store():
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _store()
