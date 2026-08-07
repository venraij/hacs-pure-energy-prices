from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import (
    CONF_ADDED_COSTS,
    CONF_BUSINESS,
    CONF_COMMODITY,
    CONF_DOUBLE_METER,
    CONF_ELEMENT_ID,
    CONF_HORIZON_HOURS,
    CONF_PERCENTILES,
    CONF_RETURN_COSTS,
    CONF_SCAN_INTERVAL,
    CONF_SOLAR_PANELS,
    CONF_UNIT_OF_MEASUREMENT,
    DEFAULT_ADDED_COSTS,
    DEFAULT_BUSINESS,
    DEFAULT_COMMODITY,
    DEFAULT_DOUBLE_METER,
    DEFAULT_ELEMENT_ID,
    DEFAULT_HORIZON_HOURS,
    DEFAULT_PERCENTILES,
    DEFAULT_RETURN_COSTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOLAR_PANELS,
    DEFAULT_UNIT_OF_MEASUREMENT,
    DOMAIN,
)


class PureEnergyPricesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def _get_schema(self, data: dict) -> vol.Schema:
        """Return the schema for the configuration form."""
        # Entry data stores percentiles as list; UI displays as comma-separated string
        p_val = data.get(CONF_PERCENTILES, DEFAULT_PERCENTILES)
        if isinstance(p_val, list):
            p_str = ", ".join(str(p) for p in p_val)
        else:
            p_str = str(p_val) if p_val is not None else DEFAULT_PERCENTILES

        return vol.Schema({
            vol.Required(CONF_ELEMENT_ID, default=DEFAULT_ELEMENT_ID): vol.Int(),
            vol.Required(CONF_DOUBLE_METER, default=DEFAULT_DOUBLE_METER): vol.Boolean(),
            vol.Required(CONF_SOLAR_PANELS, default=DEFAULT_SOLAR_PANELS): vol.Boolean(),
            vol.Required(CONF_BUSINESS, default=DEFAULT_BUSINESS): vol.Boolean(),
            vol.Required(CONF_HORIZON_HOURS, default=DEFAULT_HORIZON_HOURS): vol.Int(),
            vol.Optional(CONF_ADDED_COSTS, default=DEFAULT_ADDED_COSTS): vol.Float(),
            vol.Optional(CONF_RETURN_COSTS, default=DEFAULT_RETURN_COSTS): vol.Float(),
            vol.Optional(CONF_COMMODITY, default=DEFAULT_COMMODITY): vol.In(["electricity", "gas", "redelivery"]),
            vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): vol.In(["€/kWh", "€/m³"]),
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Int(), vol.Range(min=60, max=86400)
            ),
            vol.Optional(CONF_PERCENTILES, default=p_str): str,
        })

    def _process_input(self, user_input: dict) -> dict | None:
        """Convert string percentiles to a list of floats."""
        processed = user_input.copy()
        if isinstance(processed.get(CONF_PERCENTILES), str):
            try:
                processed[CONF_PERCENTILES] = [
                    float(p.strip()) for p in processed[CONF_PERCENTILES].split(",")
                ]
            except ValueError as e:
                from voluptuous import Invalid
                raise Invalid(f"De waarden voor PERCENTILES moeten geldige numerieke waarden zijn: {e}")
        return processed

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        # Use the built-in HA validation to capture all errors
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema({}),
            errors={}
        )

    async def async_step_reconfigure(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        # Use the built-in HA validation to capture all errors
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._get_schema(dict(self._get_reconfigure_entry().data)),
            errors={}
        )