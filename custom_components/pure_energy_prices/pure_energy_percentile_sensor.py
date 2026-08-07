import logging
import statistics
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator

_LOGGER = logging.getLogger(__name__)

class PureEnergyPercentileSensor(SensorEntity):
    """Sensor entity for displaying a specific percentile price."""
    
    def __init__(self, coordinator: PureEnergyCoordinator, config_entry: ConfigEntry, percentile: float, name: str):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.percentile = percentile
        self._name = name # Store name in a private attribute to avoid setter conflict

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        p = int(self.percentile) if self.percentile == int(self.percentile) else self.percentile
        return f"Pure Energy {p}% Percentile ({self._name})"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self.config_entry.data.get('unit_of_measurement', '€/kWh')

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the calculated percentile price as a float."""
        try:
            data_container = self.coordinator.data
            
            # Defensive extraction to handle both PureEnergyData object and mock dictionary
            prices = None
            if hasattr(data_container, 'prices'):
                prices = data_container.prices
            elif isinstance(data_container, dict) and 'prices' in data_container:
                prices = data_container['prices']
            
            if not prices:
                return None
            
            # Extract numeric prices from the list of dicts returned by the API
            prices = [p.get("price", p) if isinstance(p, dict) else p for p in prices]
            prices = [p for p in prices if isinstance(p, (int, float))]
            if not prices:
                return None

            prices.sort()
            k = (len(prices) - 1) * (self.percentile / 100.0)
            
            if k == int(k):
                return prices[int(k)]
            else:
                # Interpolate between the two closest values
                i = int(k)
                f = k - i
                return prices[i] + f * (prices[i+1] - prices[i])
        except Exception as e:
            _LOGGER.error(f"Error calculating native value for percentile {self.percentile}%: {e}")
            return None

    async def update(self) -> None:
        """Update the sensor's state based on coordinator data."""
        await self.coordinator.async_update_data()