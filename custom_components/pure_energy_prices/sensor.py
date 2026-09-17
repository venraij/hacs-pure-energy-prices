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
    CONF_SOLAR_PANELS,
    DEFAULT_PERCENTILES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class PureEnergiePriceSensor(SensorEntity):
    """Sensor entity for displaying pure energy prices."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        commodity: str,
        direction: str,
        unit_of_measurement: str,
    ) -> None:
        """Initialize the sensor."""
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"Pure Energie {commodity.title()}",
            "manufacturer": "Pure Energie",
            "model": f"Dynamic Pricing ({commodity} {direction})",
        }
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._commodity = commodity
        self._direction = direction
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{commodity}_{direction}"
        )
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_suggested_display_precision = 2

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        data = self.coordinator.data.prices if hasattr(self.coordinator, "data") and self.coordinator.data else []
        if isinstance(data, list) and len(data) > 0:
            price = data[0].get("price", 0.0)
            return round(price, 2)
        return None

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class of the sensor."""
        return SensorStateClass.TOTAL


class PureEnergiePercentileSensor(SensorEntity):
    """Sensor entity for displaying percentile prices."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        commodity: str,
        direction: str,
        unit_of_measurement: str,
        percentile: float,
    ) -> None:
        """Initialize the sensor."""
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"Pure Energie {commodity.title()}",
            "manufacturer": "Pure Energie",
            "model": f"Dynamic Pricing ({commodity} {direction})",
        }
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._commodity = commodity
        self._direction = direction
        self._percentile = percentile
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{commodity}_{direction}_percentile_{int(percentile * 100)}"
        )
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_suggested_display_precision = 2

    @property
    def native_value(self) -> float | None:
        """Return the percentile price."""
        data = self.coordinator.data.prices if hasattr(self.coordinator, "data") and self.coordinator.data else []
        if not isinstance(data, list) or len(data) == 0:
            return None

        prices = [record.get("price", 0.0) for record in data if "price" in record]
        if not prices:
            return None

        # Calculate percentile using linear interpolation
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
        return SensorStateClass.TOTAL


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the Pure Energie sensors."""
    coordinators = hass.data[DOMAIN][config_entry.entry_id]

    # Determine which sensors to create
    has_electricity = config_entry.data.get(CONF_COMMODITY_ELECTRICITY, True)
    has_solar = config_entry.data.get(CONF_SOLAR_PANELS, False)
    has_gas = config_entry.data.get(CONF_COMMODITY_GAS, False)

    # Parse percentiles
    percentiles_raw = config_entry.data.get("percentiles", DEFAULT_PERCENTILES)

    if isinstance(percentiles_raw, str):
        percentiles = [float(p.strip()) for p in percentiles_raw.split(",")]
    elif isinstance(percentiles_raw, list):
        percentiles = [float(p) for p in percentiles_raw]
    else:
        percentiles = [0.05, 0.1, 0.2, 0.4]

    sensors = []

    # Create electricity import sensor (always created if electricity is selected)
    if has_electricity and "electricity_import" in coordinators:
        sensors.append(
            PureEnergiePriceSensor(
                coordinators["electricity_import"],
                config_entry,
                "electricity",
                "import",
                "kWh",
            )
        )
        # Add percentile sensors for electricity import
        for percentile in percentiles:
            sensors.append(
                PureEnergiePercentileSensor(
                    coordinators["electricity_import"],
                    config_entry,
                    "electricity",
                    "import",
                    "kWh",
                    percentile,
                )
            )

        # Create electricity export sensor if solar panels are configured
        if has_solar and "electricity_export" in coordinators:
            sensors.append(
                PureEnergiePriceSensor(
                    coordinators["electricity_export"],
                    config_entry,
                    "electricity",
                    "export",
                    "kWh",
                )
            )
            # Add percentile sensors for electricity export
            for percentile in percentiles:
                sensors.append(
                    PureEnergiePercentileSensor(
                        coordinators["electricity_export"],
                        config_entry,
                        "electricity",
                        "export",
                        "kWh",
                        percentile,
                    )
                )

    # Create gas import sensor (only if gas is configured)
    if has_gas and "gas_import" in coordinators:
        sensors.append(
            PureEnergiePriceSensor(
                coordinators["gas_import"],
                config_entry,
                "gas",
                "import",
                "m³",
            )
        )
        # Add percentile sensors for gas import
        for percentile in percentiles:
            sensors.append(
                PureEnergiePercentileSensor(
                    coordinators["gas_import"],
                    config_entry,
                    "gas",
                    "import",
                    "m³",
                    percentile,
                )
            )

    async_add_entities(sensors)
