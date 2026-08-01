from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from voluptuous import Any

from custom_components.pure_energy_prices.const import DOMAIN
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: PureEnergyCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [
        PureEnergyCurrentPriceSensor(coordinator, config_entry),
        PureEnergyPricesScheduleSensor(coordinator, config_entry)
    ]

    # Create the sensors.
    async_add_entities(sensors)
class PureEnergyCurrentPriceSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity):
    _attr_name = "Pure Energie Current Price"
    _attr_unique_id = "pure_energy_current_price"
    _attr_unit_of_measurement = "€/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = None
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PureEnergyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        prices = data.prices or []

        current = next(
            (p for p in prices if p.get("date", {}).get("current") is True),
            None,
        )
        if not current:
            return None

        return current.get("price")

class PureEnergyPricesScheduleSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity):
    _attr_name = "Pure Energie prices schedule"
    _attr_unique_id = "pure_energy_prices_schedule"
    _attr_unit_of_measurement = "€/kWh"

    def __init__(self, coordinator: PureEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def native_value(self) -> dict:
        data = self.coordinator.data or {}
        prices = data.prices or []

        # This is the full 24h payload
        return {
            "prices_24h": prices,
        }