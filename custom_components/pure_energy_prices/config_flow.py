"""Config flow for the Pure Energie Prices integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from custom_components.pure_energy_prices.const import (
    CONF_ADDED_COSTS,
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
    CONF_DOUBLE_METER,
    CONF_GAS_ELEMENT_ID,
    CONF_HORIZON_HOURS,
    CONF_RETURN_COSTS,
    CONF_SCAN_INTERVAL,
    CONF_SOLAR_PANELS,
    DEFAULT_ADDED_COSTS,
    DEFAULT_DOUBLE_METER,
    DEFAULT_GAS_ELEMENT_ID,
    DEFAULT_HORIZON_HOURS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOLAR_PANELS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class PureEnergieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pure Energie Prices."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a user-initiated config flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title="Pure Energie",
                data=user_input,
            )

        defaults: dict[str, Any] = {}

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_COMMODITY_ELECTRICITY,
                    default=defaults.get(CONF_COMMODITY_ELECTRICITY, True),
                ): cv.boolean,
                vol.Required(
                    CONF_SOLAR_PANELS,
                    default=defaults.get(CONF_SOLAR_PANELS, DEFAULT_SOLAR_PANELS),
                ): cv.boolean,
                vol.Required(
                    CONF_COMMODITY_GAS,
                    default=defaults.get(CONF_COMMODITY_GAS, False),
                ): cv.boolean,
                vol.Required(
                    CONF_HORIZON_HOURS,
                    default=defaults.get(CONF_HORIZON_HOURS, DEFAULT_HORIZON_HOURS),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
                vol.Required(
                    CONF_GAS_ELEMENT_ID,
                    default=defaults.get(CONF_GAS_ELEMENT_ID, DEFAULT_GAS_ELEMENT_ID),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_ADDED_COSTS,
                    default=defaults.get(CONF_ADDED_COSTS, DEFAULT_ADDED_COSTS),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_RETURN_COSTS,
                    default=defaults.get(CONF_RETURN_COSTS, DEFAULT_ADDED_COSTS),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                vol.Required(
                    CONF_DOUBLE_METER,
                    default=defaults.get(CONF_DOUBLE_METER, DEFAULT_DOUBLE_METER),
                ): cv.boolean,
            },
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )


class PureEnergieOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Pure Energie Prices."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            updated_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=updated_data
            )
            return self.async_create_entry(
                title="Pure Energie",
                data=user_input,
            )

        defaults: dict[str, Any] = dict(self.config_entry.data)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_COMMODITY_ELECTRICITY,
                    default=defaults.get(CONF_COMMODITY_ELECTRICITY, True),
                ): cv.boolean,
                vol.Required(
                    CONF_SOLAR_PANELS,
                    default=defaults.get(CONF_SOLAR_PANELS, DEFAULT_SOLAR_PANELS),
                ): cv.boolean,
                vol.Required(
                    CONF_COMMODITY_GAS,
                    default=defaults.get(CONF_COMMODITY_GAS, False),
                ): cv.boolean,
                vol.Required(
                    CONF_HORIZON_HOURS,
                    default=defaults.get(CONF_HORIZON_HOURS, DEFAULT_HORIZON_HOURS),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
                vol.Required(
                    CONF_GAS_ELEMENT_ID,
                    default=defaults.get(CONF_GAS_ELEMENT_ID, DEFAULT_GAS_ELEMENT_ID),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_ADDED_COSTS,
                    default=defaults.get(CONF_ADDED_COSTS, DEFAULT_ADDED_COSTS),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_RETURN_COSTS,
                    default=defaults.get(CONF_RETURN_COSTS, DEFAULT_ADDED_COSTS),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                vol.Required(
                    CONF_DOUBLE_METER,
                    default=defaults.get(CONF_DOUBLE_METER, DEFAULT_DOUBLE_METER),
                ): cv.boolean,
            },
        )

        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
