import logging
import math
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.pure_energy_prices.const import DOMAIN
from .pure_energy_price_sensor import PureEnergyPriceSensor
from .pure_energy_percentile_sensor import PureEnergyPercentileSensor
from .coordinator import PureEnergyCoordinator

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_UNIT_OF_MEASUREMENT,
    CONF_PERCENTILES,
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: PureEnergyCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors: list[SensorEntity] = [
        PureEnergyPriceSensor(coordinator, config_entry),
    ]

    percentiles = config_entry.data.get(CONF_PERCENTILES)
    if isinstance(percentiles, list):
        for percentile in percentiles:
            sensors.append(
                PureEnergyPercentileSensor(coordinator, config_entry, percentile, f"{percentile}%")
            )

