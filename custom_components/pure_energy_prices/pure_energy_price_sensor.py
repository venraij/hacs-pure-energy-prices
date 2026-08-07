import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator

_LOGGER = logging.getLogger(__name__)

class PureEnergyPriceSensor(SensorEntity):
    """Sensor entity for displaying pure energy prices."""
    
    def __init__(self, coordinator: PureEnergyCoordinator, config_entry: ConfigEntry):
        self.coordinator = coordinator
        self.config_entry = config_entry

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"Pure Energy Price ({self.config_entry.entry_id})"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self.config_entry.data.get('unit_of_measurement', '€/kWh')

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def state(self) -> str:
        """Return the current price as a string."""
        data = self.coordinator.data.prices
        if data:
            # Assume the price is the first item in the list
            price = data[0].get("price", 0.0)
            return f"{price:.2f}"
        return "unavailable"

    async def update(self) -> None:
        """Update the sensor's state based on coordinator data."""
        self.coordinator.async_update_data()