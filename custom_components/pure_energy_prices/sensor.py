from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.entity import EntityDescription
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAIN = "pure_energy_custom"

API_URL = (
    "https://pure-energie.nl/api/prices-element/dynamic/"
    "?double_meter=true&solar_panels=true&commodity=electricity"
    "&current=null&business=false&element_id=11480"
)

SCAN_INTERVAL = 3600  # seconds


@dataclass
class PureEnergyData:
    prices: list[dict[str, Any]]


class PureEnergyCoordinator(DataUpdateCoordinator[PureEnergyData]):
    def __init__(self, hass: HomeAssistant):
        super().__init__(
            hass,
            _LOGGER,
            name="Pure Energie prices",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.data = PureEnergyData(prices=[])

    async def _async_update_data(self) -> PureEnergyData:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, timeout=30) as resp:
                resp.raise_for_status()
                payload = await resp.json()

        prices = payload.get("prices", []) or []
        return PureEnergyData(prices=prices)


class PureEnergyPricesSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity):
    _attr_name = "Pure Energie prices"
    _attr_unique_id = "pure_energy_prices_custom"
    _attr_unit_of_measurement = "€ / kWh"
    _attr_native_unit_of_measurement = "€ / kWh"
    _attr_should_poll = False

    def __init__(self, coordinator: PureEnergyCoordinator):
        super().__init__(coordinator)

        # set a value; we’ll primarily use attributes (prices list)
        self._attr_native_value = None

    @property
    def native_value(self):
        # Keep value optional; apexcharts will use attributes.prices
        return None

    @property
    def extra_state_attributes(self):
        return {
            "prices": self.coordinator.data.prices,
        }


class PureEnergyCurrentAllInSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity):
    _attr_name = "Pure Energie current all-in price"
    _attr_unique_id = "pure_energy_current_all_in_price_custom"
    _attr_unit_of_measurement = "€ / kWh"
    _attr_should_poll = False

    def __init__(self, coordinator: PureEnergyCoordinator):
        super().__init__(coordinator)
        self._attr_native_value = None

    @property
    def native_value(self):
        prices = self.coordinator.data.prices or []
        current = next((r for r in prices if r.get("date", {}).get("current") is True), None)
        if not current:
            return None
        return float(current.get("price", 0))


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Fallback platform-style setup if you want to use YAML discovery later.
    coordinator = PureEnergyCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        PureEnergyPricesSensor(coordinator),
        PureEnergyCurrentAllInSensor(coordinator),
    ])


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = PureEnergyCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        PureEnergyPricesSensor(coordinator),
        PureEnergyCurrentAllInSensor(coordinator),
    ])
