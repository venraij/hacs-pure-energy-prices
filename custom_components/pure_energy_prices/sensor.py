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
        return self.config_entry.data.get("unit_of_measurement", "€/kWh")
    
    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> str | None:
        """Return the current price as a string."""
        data = self.coordinator.data.prices if hasattr(self.coordinator, "data") and self.coordinator.data else []
        if isinstance(data, list) and len(data) > 0:
            price = data[0].get("price", 0.0)
            return f"{price:.2f}"
        return None

    async def update(self) -> None:
        """Update the sensor's state based on coordinator data."""


class PureEnergyPercentileSensor(SensorEntity):
    """Sensor entity for displaying a specific percentile price."""

    def __init__(self, coordinator: PureEnergyCoordinator, config_entry: ConfigEntry, percentile: float):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.percentile = percentile

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        p_val = int(self.percentile) if isinstance(self.percentile, float) and self.percentile == int(self.percentile) else self.percentile
        return f"Pure Energy {p_val}% Percentile ({self.percentile}%)"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self.config_entry.data.get("unit_of_measurement", "€/kWh")

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the calculated percentile price as a float."""
        try:
            data_container = self.coordinator.data if hasattr(self.coordinator, "data") else {}

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

            # Calculate percentile using linear interpolation
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the Sensors."""

    # Get the coordinator from hass.data (set in __init__.py)
    coordinator = PureEnergyCoordinator(hass=hass, entry=config_entry)

    await coordinator.async_config_entry_first_refresh()

    if not hasattr(coordinator, 'data') or not coordinator.data:
        _LOGGER.error("No data available for sensors")
        return

    # Create the main price sensor
    sensors: list[SensorEntity] = [PureEnergyPriceSensor(coordinator, config_entry)]

    # Add percentile sensors based on configuration
    percentiles_str = config_entry.data.get('percentiles', '0.05, 0.1, 0.2, 0.4')
    
    if isinstance(percentiles_str, str):
        percentiles = [float(p.strip()) for p in percentiles_str.split(',')]
    elif isinstance(percentiles_str, list):
        percentiles = [float(p) for p in percentiles_str]
    else:
        # Default to standard percentiles if parsing fails
        default_percentiles = ['0.05', '0.1', '0.2', '0.4']
        percentiles = [float(p.strip()) for p in default_percentiles]

    for percentile in percentiles:
        sensors.append(
            PureEnergyPercentileSensor(coordinator, config_entry, percentile)
        )

    async_add_entities(sensors)