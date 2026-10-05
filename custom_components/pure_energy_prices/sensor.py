"""Sensor entities for the Pure Energie Prices integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.pure_energy_prices.const import (
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
    CONF_PERCENTILES,
    CONF_SOLAR_PANELS,
    DEFAULT_PERCENTILES,
    DOMAIN,
    UNIT_EUR_KWH,
    UNIT_EUR_M3,
)

_LOGGER = logging.getLogger(__name__)


class PureEnergiePriceSensor(SensorEntity):
    """Sensor entity for displaying pure energy prices."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        commodity: str = "electricity",
        direction: str = "import",
        unit_of_measurement: str = UNIT_EUR_KWH,
    ) -> None:
        """Initialize the sensor."""
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Pure Energie",
            "manufacturer": "Pure Energie",
            "model": f"Dynamic Pricing ({commodity} {direction})",
        }
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._commodity = commodity
        self._direction = direction
        self._attr_name = f"{commodity.title()} {direction.title()}"
        self._attr_unique_id = f"{config_entry.entry_id}_{commodity}_{direction}"
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_suggested_display_precision = 2

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        data = self.coordinator.data.prices if hasattr(self.coordinator, "data") and self.coordinator.data else []
        if not data or not isinstance(data, list):
            return None
        # Try to find the entry marked as current by the API
        for entry in data:
            date_info = entry.get("date", {})
            if isinstance(date_info, dict) and date_info.get("current"):
                return round(entry.get("price", 0.0), 2)
        # Fallback: use the first entry (e.g., if API didn't mark any as current)
        if len(data) > 0:
            return round(data[0].get("price", 0.0), 2)
        return None

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the price history for graphing."""
        data = self.coordinator.data.prices if hasattr(self.coordinator, "data") and self.coordinator.data else []
        return {"prices": data}


class PureEnergiePercentileSensor(SensorEntity):
    """Sensor entity for displaying percentile prices."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        commodity: str = "electricity",
        direction: str = "import",
        unit_of_measurement: str = UNIT_EUR_KWH,
        percentile: float = 0.1,
    ) -> None:
        """Initialize the sensor."""
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Pure Energie",
            "manufacturer": "Pure Energie",
            "model": f"Dynamic Pricing ({commodity} {direction})",
        }
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._commodity = commodity
        self._direction = direction
        self._percentile = percentile
        self._attr_name = f"{commodity.title()} Percentile Price ({int(percentile * 100)}%)"
        self._attr_unique_id = f"{config_entry.entry_id}_{commodity}_{direction}_percentile_{int(percentile * 100)}"
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_suggested_display_precision = 2

    @property
    def native_value(self) -> float | None:
        """Return the percentile price."""
        data = self.coordinator.data.prices if hasattr(self.coordinator, "data") and self.coordinator.data else []
        if not data:
            return None
        # Include all non-zero prices, including future data if provided by API
        prices = []
        for record in data:
            if "price" not in record:
                continue
            price = record.get("price", 0.0)
            if price == 0:
                continue
            prices.append(price)
        if not prices:
            return None
        prices = sorted(prices)
        k = (len(prices) - 1) * self._percentile
        idx = int(k)
        fraction = k - idx
        if idx >= len(prices) - 1:
            return round(prices[-1], 2)
        if fraction == 0:
            return round(prices[idx], 2)
        return round(prices[idx] + fraction * (prices[idx + 1] - prices[idx]), 2)

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the Pure Energie sensors."""
    coordinators = hass.data[DOMAIN][config_entry.entry_id]

    has_electricity = config_entry.data.get(CONF_COMMODITY_ELECTRICITY, True)
    has_solar = config_entry.data.get(CONF_SOLAR_PANELS, False)
    has_gas = config_entry.data.get(CONF_COMMODITY_GAS, False)

    percentiles_raw = config_entry.data.get(CONF_PERCENTILES, DEFAULT_PERCENTILES)
    if isinstance(percentiles_raw, str):
        percentiles = [float(p.strip()) for p in percentiles_raw.split(",")]
    elif isinstance(percentiles_raw, list):
        percentiles = [float(p) for p in percentiles_raw]
    else:
        percentiles = [0.05, 0.1, 0.2, 0.4]

    sensors = []

    if has_electricity and "electricity_import" in coordinators:
        sensors.append(PureEnergiePriceSensor(coordinators["electricity_import"], config_entry, "electricity", "import", UNIT_EUR_KWH))
        for p in percentiles:
            sensors.append(PureEnergiePercentileSensor(coordinators["electricity_import"], config_entry, "electricity", "import", UNIT_EUR_KWH, p))

    if has_solar and "electricity_export" in coordinators:
        sensors.append(PureEnergiePriceSensor(coordinators["electricity_export"], config_entry, "redelivery", "export", UNIT_EUR_KWH))
        for p in percentiles:
            sensors.append(PureEnergiePercentileSensor(coordinators["electricity_export"], config_entry, "redelivery", "export", UNIT_EUR_KWH, p))

    if has_gas and "gas_import" in coordinators:
        sensors.append(PureEnergiePriceSensor(coordinators["gas_import"], config_entry, "gas", "import", UNIT_EUR_M3))
        for p in percentiles:
            sensors.append(PureEnergiePercentileSensor(coordinators["gas_import"], config_entry, "gas", "import", UNIT_EUR_M3, p))

    async_add_entities(sensors)
