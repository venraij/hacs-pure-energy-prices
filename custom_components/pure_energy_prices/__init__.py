from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry
from custom_components.pure_energy_prices.coordinator import PureEnergieConfigEntry
from custom_components.pure_energy_prices.sensor import PureEnergyCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: PureEnergieConfigEntry) -> bool:
    coordinator = PureEnergyCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data.prices:
        raise ConfigEntryNotReady("No prices data available from Pure Energie API")

    entry.async_on_unload(
        entry.add_update_listener(_async_update_listener)
    )
    
    # Load the sensor platform for this entry    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Delete device if selected from UI."""
    # Adding this function shows the delete device option in the UI.
    # Remove this function if you do not want that option.
    # You may need to do some checks here before allowing devices to be removed.
    return True

async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config options update."""
    # Reload the integration when the options change.
    await hass.config_entries.async_reload(entry.entry_id)