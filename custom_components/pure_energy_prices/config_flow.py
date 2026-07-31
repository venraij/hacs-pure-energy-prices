from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_ELEMENT_ID,
    CONF_DOUBLE_METER,
    CONF_SOLAR_PANELS,
    CONF_BUSINESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_ELEMENT_ID,
    DEFAULT_DOUBLE_METER,
    DEFAULT_SOLAR_PANELS,
    DEFAULT_BUSINESS,
    DEFAULT_SCAN_INTERVAL,
)

class PureEnergyPricesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="Pure Energie Prices",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_ELEMENT_ID, default=DEFAULT_ELEMENT_ID): int,
                vol.Required(CONF_DOUBLE_METER, default=DEFAULT_DOUBLE_METER): bool,
                vol.Required(CONF_SOLAR_PANELS, default=DEFAULT_SOLAR_PANELS): bool,
                vol.Required(CONF_BUSINESS, default=DEFAULT_BUSINESS): bool,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    int, vol.Range(min=60, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        # Optional; omit options flow by returning None if you prefer.
        return None
