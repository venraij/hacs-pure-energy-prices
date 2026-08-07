from __future__ import annotations

import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.pure_energy_prices.const import DOMAIN
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_UNIT_OF_MEASUREMENT,
    CONF_PERCENTILES,
)

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
    sensors: list[SensorEntity] = [
        PureEnergyPriceSensor(coordinator, config_entry),
    ]

    percentiles = config_entry.data.get(CONF_PERCENTILES)
    if isinstance(percentiles, list):
        for percentile in percentiles:
            sensors.append(
                PureEnergyPercentileSensor(
                    coordinator, config_entry, percentile, f"{int(percentile * 100)}% price low"
                )
            )

    # Create the sensors.
    async_add_entities(sensors)
    return True
class PureEnergyPriceSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity): # type: ignore
    _attr_name = "Pure Energie Price"
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
        self._attr_unique_id = f"pure_energie_prices_{entry.entry_id}"
        self._attr_unit_of_measurement = entry.data.get(CONF_UNIT_OF_MEASUREMENT)

    @property  # type: ignore
    def native_value(self) -> float | None: # type: ignore
        data = self.coordinator.data or {}
        prices = data.prices or []

        current = next(
            (p for p in prices if p.get("date", {}).get("current") is True),
            None,
        )
        if not current:
            return None

        return current.get("price")

    @property  # type: ignore
    def extra_state_attributes(self) -> dict: # type: ignore
        data = self.coordinator.data or {}
        prices = data.prices or []

        # This is the full 24h payload
        return {
            "prices": prices,
        }

class PureEnergyPercentileSensor(CoordinatorEntity[PureEnergyCoordinator], SensorEntity): # type: ignore
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PureEnergyCoordinator,
        entry: ConfigEntry,
        percentile: float,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._percentile = percentile
        self._attr_name = name
        self._attr_unique_id = f"pure_energie_prices_percentile_{entry.entry_id}_{percentile}"
        self._attr_unit_of_measurement = entry.data.get(CONF_UNIT_OF_MEASUREMENT)

    @property
    def native_value(self) -> float | None: # type: ignore
        data = self.coordinator.data or {}
        prices = data.prices or []

        if not prices:
            return None

        # Find the current date from the 'current' price if available
        current_price_entry = next(
            (p for p in prices if p.get("date", {}).get("current") is True),
            None,
        )
        
        if not current_price_entry:
            return None
            
        current_date_str = current_price_entry.get("date", {}).get("full", "").split(" ")[0]
        
        if not current_date_str:
            return None

        day_prices: list[float] = [
            float(p.get("price", 0.0))
            for p in prices
            if p.get("date", {}).get("full", "").startswith(current_date_str)
            and p.get("price") is not None
        ]

        if not day_prices:
            return None

        if len(day_prices) < 2:
            return day_prices[0]

        try:
            sorted_prices = sorted(day_prices)
            
            # Calculate the number of lowest prices to average (P% of N)
            # We use ceil to ensure we include at least the required percentage.
            target_count = math.ceil((self._percentile / 100) * len(sorted_prices))
            
            if target_count == 0:
                return None
            
            # Average the cheapest 'target_count' prices
            average_low = sum(sorted_prices[:target_count]) / target_count
            return average_low

        except Exception as e:
            _LOGGER.error("Error calculating average low for %s: %s", self._attr_name, e)
            return None

    @property
    def extra_state_attributes(self) -> dict: # type: ignore
        data = self.coordinator.data or {}
        prices = data.prices or []

        return {
            "prices": prices,
        }

        