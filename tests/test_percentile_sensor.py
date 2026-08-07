"""Tests for the pure_energy_percentile_sensor module."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from custom_components.pure_energy_prices.pure_energy_percentile_sensor import PureEnergyPercentileSensor


class TestPureEnergyPercentileSensor:
    """Test cases for the PureEnergyPercentileSensor class."""

    @pytest.fixture
    def mock_entry(self):
        """Create a mock config entry."""
        entry = MagicMock()
        entry.data = {"unit_of_measurement": "€/kWh"}
        entry.entry_id = "test_entry"
        return entry

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator with sample data."""
        coord = MagicMock()
        coord.data.prices = [
            {"price": 0.10},
            {"price": 0.15},
            {"price": 0.20},
            {"price": 0.25},
            {"price": 0.30},
        ]
        coord.async_update_data = AsyncMock()
        return coord

    @pytest.fixture
    def percentile_sensor(self, mock_coordinator, mock_entry):
        """Create a percentile sensor instance."""
        return PureEnergyPercentileSensor(
            mock_coordinator, mock_entry, 10.0, "10%"
        )

    def test_sensor_creation(self, percentile_sensor):
        """Test sensor creation."""
        assert percentile_sensor.percentile == 10.0
        assert percentile_sensor.name == "Pure Energy 10% Percentile (10%)"

    def test_unit_of_measurement(self, percentile_sensor, mock_entry):
        """Test unit of measurement property."""
        assert percentile_sensor.unit_of_measurement == "€/kWh"

    def test_state_class(self, percentile_sensor):
        """Test state class property."""
        from homeassistant.components.sensor import SensorStateClass
        assert percentile_sensor.state_class == SensorStateClass.MEASUREMENT

    def test_native_value_with_data(self, percentile_sensor, mock_coordinator):
        """Test native_value with available data."""
        # Set up mock data directly on the coordinator's data attribute
        mock_coordinator.data.prices = [0.10, 0.15, 0.20, 0.25, 0.30]
        value = percentile_sensor.native_value
        assert value is not None
        assert isinstance(value, float)

    def test_native_value_empty_data(self, percentile_sensor):
        """Test native_value with no data."""
        percentile_sensor.coordinator.data.prices = []
        value = percentile_sensor.native_value
        assert value is None

    @pytest.mark.asyncio
    async def test_update(self, percentile_sensor):
        """Test update method."""
        await percentile_sensor.update()
        # Verify that the coordinator's async_update_data was called
        assert percentile_sensor.coordinator.async_update_data.called