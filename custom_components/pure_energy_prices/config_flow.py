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
    DEFAULT_ELEMENT_ID,
    DEFAULT_DOUBLE_METER,
    DEFAULT_SOLAR_PANELS,
    DEFAULT_BUSINESS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_HORIZON_HOURS,
    DEFAULT_ADDED_COSTS,
    DEFAULT_RETURN_COSTS,
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
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All( # type: ignore
                    int, vol.Range(min=60, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

