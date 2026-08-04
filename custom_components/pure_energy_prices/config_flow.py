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

    def _get_normalized_data(self, data: dict) -> dict:
        """Ensure all data has the correct types and defaults before schema creation."""
        try:
            normalized = {
                CONF_ELEMENT_ID: int(data.get(CONF_ELEMENT_ID, DEFAULT_ELEMENT_ID)),
                CONF_DOUBLE_METER: bool(data.get(CONF_DOUBLE_METER, DEFAULT_DOUBLE_METER)),
                CONF_SOLAR_PANELS: bool(data.get(CONF_SOLAR_PANELS, DEFAULT_SOLAR_PANELS)),
                CONF_BUSINESS: bool(data.get(CONF_BUSINESS, DEFAULT_BUSINESS)),
                CONF_HORIZON_HOURS: int(data.get(CONF_HORIZON_HOURS, DEFAULT_HORIZON_HOURS)),
                CONF_ADDED_COSTS: float(data.get(CONF_ADDED_COSTS, DEFAULT_ADDED_COSTS)),
                CONF_RETURN_COSTS: float(data.get(CONF_RETURN_COSTS, DEFAULT_RETURN_COSTS)),
                CONF_COMMODITY: data.get(CONF_COMMODITY, DEFAULT_COMMODITY),
                CONF_UNIT_OF_MEASUREMENT: data.get(CONF_UNIT_OF_MEASUREMENT, DEFAULT_UNIT_OF_MEASUREMENT),
                CONF_SCAN_INTERVAL: int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
            }

            # Handle percentiles separately: convert list to comma-separated string for UI
            p_val = data.get(CONF_PERCENTILES, DEFAULT_PERCENTILES)
            if isinstance(p_val, list):
                normalized[CONF_PERCENTILES] = ", ".join(map(str, p_val))
            elif p_val is None:
                normalized[CONF_PERCENTILES] = DEFAULT_PERCENTILES
            else:
                normalized[CONF_PERCENTILES] = str(p_val)

            return normalized
        except (ValueError, TypeError):
            # If casting fails, return a dictionary of defaults to prevent 500 error
            return {
                CONF_ELEMENT_ID: DEFAULT_ELEMENT_ID,
                CONF_DOUBLE_METER: DEFAULT_DOUBLE_METER,
                CONF_SOLAR_PANELS: DEFAULT_SOLAR_PANELS,
                CONF_BUSINESS: DEFAULT_BUSINESS,
                CONF_HORIZON_HOURS: DEFAULT_HORIZON_HOURS,
                CONF_ADDED_COSTS: DEFAULT_ADDED_COSTS,
                CONF_RETURN_COSTS: DEFAULT_RETURN_COSTS,
                CONF_COMMODITY: DEFAULT_COMMODITY,
                CONF_UNIT_OF_MEASUREMENT: DEFAULT_UNIT_OF_MEASUREMENT,
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                CONF_PERCENTILES: DEFAULT_PERCENTILES,
            }

    def _get_schema(self, data: dict) -> vol.Schema:
        """Return the schema for the configuration form."""
        norm = self._get_normalized_data(data)

        return vol.Schema(
            {
                vol.Required(CONF_ELEMENT_ID, default=norm[CONF_ELEMENT_ID]): int,
                vol.Required(CONF_DOUBLE_METER, default=norm[CONF_DOUBLE_METER]): bool,
                vol.Required(CONF_SOLAR_PANELS, default=norm[CONF_SOLAR_PANELS]): bool,
                vol.Required(CONF_BUSINESS, default=norm[CONF_BUSINESS]): bool,
                vol.Required(CONF_HORIZON_HOURS, default=norm[CONF_HORIZON_HOURS]): int,
                vol.Optional(CONF_ADDED_COSTS, default=norm[CONF_ADDED_COSTS]): float,
                vol.Optional(CONF_RETURN_COSTS, default=norm[CONF_RETURN_COSTS]): float,
                vol.Optional(CONF_COMMODITY, default=norm[CONF_COMMODITY]): vol.In(["electricity", "gas", "redelivery"]),
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=norm[CONF_UNIT_OF_MEASUREMENT]): vol.In(["€/kWh", "€/m³"]),
                vol.Optional(CONF_SCAN_INTERVAL, default=norm[CONF_SCAN_INTERVAL]): vol.All(
                    int, vol.Range(min=60, max=86400)
                ),
                vol.Optional(CONF_PERCENTILES, default=norm[CONF_PERCENTILES]): str,
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
