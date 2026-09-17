"""The Pure Energie Prices integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import (
    DeviceEntry,
    DeviceEntryType,
    async_get as async_get_device_registry,
)
from custom_components.pure_energy_prices.const import (
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
    CONF_COMMODITY_REDELIVERY,
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
from custom_components.pure_energy_prices.coordinator import (
    PureEnergyCoordinator,
)

# Type alias for config entry
PureEnergieConfigEntry = ConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: PureEnergieConfigEntry) -> bool:
    """Set up Pure Energie Prices from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Handle migration from old config format
    if CONF_COMMODITY_REDELIVERY in entry.data:
        _LOGGER.info("Detected old config format, migrating...")
        old_commodity = entry.data.get(CONF_COMMODITY_REDELIVERY, "electricity")
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_COMMODITY_ELECTRICITY: old_commodity == "electricity",
                CONF_COMMODITY_GAS: old_commodity == "gas",
            },
            options={},
        )

    # Create coordinators for each configured commodity
    coordinators = {}

    # Electricity import (always created if electricity is configured)
    if entry.data.get(CONF_COMMODITY_ELECTRICITY, True):
        coordinators["electricity_import"] = PureEnergyCoordinator(
            hass,
            entry,
            element_id=None,  # Will use DEFAULT_ELEMENT_ID
            commodity="electricity",
            direction="import",
        )
        await coordinators["electricity_import"].async_config_entry_first_refresh()

        # Electricity export (only if solar panels configured)
        if entry.data.get(CONF_SOLAR_PANELS, DEFAULT_SOLAR_PANELS):
            coordinators["electricity_export"] = PureEnergyCoordinator(
                hass,
                entry,
                element_id=None,
                commodity="electricity",
                direction="export",
            )
            await coordinators["electricity_export"].async_config_entry_first_refresh()

    # Gas import (optional)
    if entry.data.get(CONF_COMMODITY_GAS, False):
        gas_element_id = entry.data.get(
            CONF_GAS_ELEMENT_ID, DEFAULT_GAS_ELEMENT_ID
        )
        coordinators["gas_import"] = PureEnergyCoordinator(
            hass,
            entry,
            element_id=gas_element_id,
            commodity="gas",
            direction="import",
        )
        await coordinators["gas_import"].async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinators

    # Register the device in the device registry
    device_registry = async_get_device_registry(hass)
    for coordinator in coordinators.values():
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Pure Energie {coordinator.commodity.title()}",
            manufacturer="Pure Energie",
            model=f"Dynamic Pricing ({coordinator.commodity} {coordinator.direction})",
            entry_type=DeviceEntryType.SERVICE,
        )

    entry.async_on_unload(
        entry.add_update_listener(
            lambda hass, config_entry: _async_options_updated(hass, config_entry)
        ),
    )

    # Load the sensor platform for this entry
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PureEnergieConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Delete device if selected from UI."""
    return True


async def _async_options_updated(hass: HomeAssistant, entry: PureEnergieConfigEntry) -> None:
    """Handle config options update."""
    # Reload the integration when the options change.
    await hass.config_entries.async_reload(entry.entry_id)
