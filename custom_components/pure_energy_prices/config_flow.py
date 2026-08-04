from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigFlowResult,
    ConfigEntry,
)

from .const import (
    DOMAIN,
    CONF_ELEMENT_ID,
    CONF_DOUBLE_METER,
    CONF_SOLAR_PANELS,
    CONF_BUSINESS,
    CONF_SCAN_INTERVAL,
    CONF_HORIZON_HOURS,
    CONF_ADDED_COSTS,
    CONF_RETURN_COSTS,
    CONF_COMMODITY,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_PERCENTILES,
    DEFAULT_ELEMENT_ID,
    DEFAULT_DOUBLE_METER,
    DEFAULT_SOLAR_PANELS,
    DEFAULT_BUSINESS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_HORIZON_HOURS,
    DEFAULT_ADDED_COSTS,
    DEFAULT_RETURN_COSTS,
    DEFAULT_COMMODITY,
    DEFAULT_UNIT_OF_MEASUREMENT,
    DEFAULT_PERCENTILES,
)

class PureEnergyPricesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def _get_schema(self, data: dict) -> vol.Schema:
        """Return the schema for the configuration form."""
        # For percentiles, if it's already a list (from existing entry), 
        # convert it to a comma-separated string for the UI.
        percentiles_val = data.get(CONF_PERCENTILES, DEFAULT_PERCENTILES)
        if isinstance(percentiles_val, list):
            percentiles_val = ", ".join(map(str, percentiles_val))

        return vol.Schema(
            {
                vol.Required(CONF_ELEMENT_ID, default=data.get(CONF_ELEMENT_ID, DEFAULT_ELEMENT_ID)): int, # type: ignore
                vol.Required(CONF_DOUBLE_METER, default=data.get(CONF_DOUBLE_METER, DEFAULT_DOUBLE_METER)): bool, # type: ignore
                vol.Required(CONF_SOLAR_PANELS, default=data.get(CONF_SOLAR_PANELS, DEFAULT_SOLAR_PANELS)): bool, # type: ignore
                vol.Required(CONF_BUSINESS, default=data.get(CONF_BUSINESS, DEFAULT_BUSINESS)): bool, # type: ignore
                vol.Required(CONF_HORIZON_HOURS, default=data.get(CONF_HORIZON_HOURS, DEFAULT_HORIZON_HOURS)): int,
                vol.Optional(CONF_ADDED_COSTS, default=data.get(CONF_ADDED_COSTS, DEFAULT_ADDED_COSTS)): float, # type: ignore
                vol.Optional(CONF_RETURN_COSTS, default=data.get(CONF_RETURN_COSTS, DEFAULT_RETURN_COSTS)): float, # type: ignore
                vol.Optional(CONF_COMMODITY, default=data.get(CONF_COMMODITY, DEFAULT_COMMODITY)): vol.In(["electricity", "gas", "redelivery"]), # type: ignore
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=data.get(CONF_UNIT_OF_MEASUREMENT, DEFAULT_UNIT_OF_MEASUREMENT)): vol.In(["€/kWh", "€/m³"]), # type: ignore
                vol.Optional(CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All( # type: ignore
                    int, vol.Range(min=60, max=86400)
                ),
                vol.Optional(CONF_PERCENTILES, default=percentiles_val): str,
            }
        )

    def _process_input(self, user_input: dict) -> dict | None:
        """Convert string percentiles to a list of floats."""
        processed = user_input.copy()
        if isinstance(processed.get(CONF_PERCENTILES), str):
            try:
                processed[CONF_PERCENTILES] = [
                    float(p.strip()) for p in processed[CONF_PERCENTILES].split(",")
                ]
            except ValueError:
                return None
        return processed

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        if user_input is not None:
            processed = self._process_input(user_input)
            if processed is None:
                return self.async_abort()

            return self.async_create_entry(
                title="Pure Energie Prices",
                data=processed,
            )

        return self.async_show_form(step_id="user", data_schema=self._get_schema({}))

    async def async_step_reconfigure(
        self, entry: ConfigEntry, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle re-configuration of an existing entry."""
        if user_input is not None:
            processed = self._process_input(user_input)
            if processed is None:
                return self.async_abort()

            return self.async_update_entry(entry, data=processed)

        return self.async_show_form(
            step_id="reconfigure", data_schema=self._get_schema(entry.data)
        )
