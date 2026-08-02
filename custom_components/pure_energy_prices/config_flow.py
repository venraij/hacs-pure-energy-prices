from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigFlowResult,
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

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="Pure Energie Prices",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_ELEMENT_ID, default=DEFAULT_ELEMENT_ID): int, # type: ignore
                vol.Required(CONF_DOUBLE_METER, default=DEFAULT_DOUBLE_METER): bool, # type: ignore
                vol.Required(CONF_SOLAR_PANELS, default=DEFAULT_SOLAR_PANELS): bool, # type: ignore
                vol.Required(CONF_BUSINESS, default=DEFAULT_BUSINESS): bool, # type: ignore
                vol.Required(CONF_HORIZON_HOURS, default=DEFAULT_HORIZON_HOURS): int,
                vol.Optional(CONF_ADDED_COSTS, default=DEFAULT_ADDED_COSTS): float, # type: ignore
                vol.Optional(CONF_RETURN_COSTS, default=DEFAULT_RETURN_COSTS): float, # type: ignore
                vol.Optional(CONF_COMMODITY, default=DEFAULT_COMMODITY): vol.In(["electricity", "gas", "redelivery"]), # type: ignore
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): vol.In(["€/kWh", "€/m³"]), # type: ignore
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All( # type: ignore
                    int, vol.Range(min=60, max=86400)
                ),
                vol.Optional(CONF_PERCENTILES, default=DEFAULT_PERCENTILES): [
                    vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0))
                ],
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

