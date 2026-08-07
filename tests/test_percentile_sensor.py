"""Unit tests for PureEnergyPercentileSensor calculation logic."""

import pytest
import math
from custom_components.pure_energy_prices.sensor import PureEnergyPercentileSensor
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator
from custom_components.pure_energy_prices.const import CONF_UNIT_OF_MEASUREMENT, CONF_PERCENTILES

# Mock objects for dependencies
class MockConfigEntry:
    def __init__(self, data: dict):
        self.data = data
        self.entry_id = 1

class MockCoordinator:
    def __init__(self):
        # Using a dictionary internally
        self._data = {"prices": []}

    @property
    def data(self):
        # This ensures the sensor accesses data via a property getter
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

# Helper to create a sensor instance
def create_sensor(coordinator: MockCoordinator, entry: MockConfigEntry, percentile: float, name: str) -> PureEnergyPercentileSensor:
    return PureEnergyPercentileSensor(coordinator, entry, percentile, name)

def mock_prices(data: list[dict]) -> dict:
    # Returns a dictionary matching the expected structure for the coordinator's data
    return {"prices": data}

@pytest.fixture
def mock_entry():
    # Use a minimal config entry for testing calculation
    return MockConfigEntry({"unit_of_measurement": "€/kWh"})

@pytest.fixture
def mock_coordinator(mock_entry):
    # Instantiate the coordinator mock
    coordinator = MockCoordinator()
    # Ensure its data is set up correctly before tests run
    return coordinator

# --- Basic Functionality & Interpolation Accuracy Tests ---

def test_percentile_basic_functionality(mock_coordinator, mock_entry):
    # Test simple case (e.g., median or a specific point)
    prices = [
        {"date": {"current": True, "full": "2024-01-01 00:00"}, "price": 1.0},
        {"date": {"current": False, "full": "2024-01-01 01:00"}, "price": 2.0},
        {"date": {"current": False, "full": "2024-01-01 02:00"}, "price": 3.0},
        {"date": {"current": False, "full": "2024-01-01 03:00"}, "price": 4.0},
        {"date": {"current": False, "full": "2024-01-01 04:00"}, "price": 5.0},
    ]
    
    # Test for 50th percentile (median, should be 3.0)
    mock_coordinator.data = mock_prices(prices)
    sensor = create_sensor(mock_coordinator, mock_entry, 50.0, "50% price low")
    assert sensor.native_value == 3.0

def test_percentile_interpolation_accuracy(mock_coordinator, mock_entry):
    # Test interpolation case (e.g., 25th percentile)
    prices = [
        {"date": {"current": True, "full": "2024-01-01 00:00"}, "price": 1.0},
        {"date": {"current": False, "full": "2024-01-01 01:00"}, "price": 2.0},
        {"date": {"current": False, "full": "2024-01-01 02:00"}, "price": 3.0},
        {"date": {"current": False, "full": "2024-01-01 03:00"}, "price": 4.0},
        {"date": {"current": False, "full": "2024-01-01 04:00"}, "price": 5.0},
    ]
    
    # Sorted prices: [1.0, 2.0, 3.0, 4.0, 5.0]
    # Index for 25% (0.25 * 4 = 1): Should be 2.0
    mock_coordinator.data = mock_prices(prices)
    sensor = create_sensor(mock_coordinator, mock_entry, 25.0, "25% price low")
    assert sensor.native_value == 2.0

    # Test interpolation (e.g., 33.33% percentile)
    prices_for_interpolation = [
        {"date": {"current": True, "full": "2024-01-01 00:00"}, "price": 1.0},
        {"date": {"current": False, "full": "2024-01-01 01:00"}, "price": 2.0},
        {"date": {"current": False, "full": "2024-01-01 02:00"}, "price": 3.0},
        {"date": {"current": False, "full": "2024-01-01 03:00"}, "price": 4.0},
        {"date": {"current": False, "full": "2024-01-01 04:00"}, "price": 5.0},
    ]
    mock_coordinator.data = mock_prices(prices_for_interpolation)
    sensor = create_sensor(mock_coordinator, mock_entry, 33.33, "33.33% price low")
    expected_value = 2.333333333333333
    assert abs(sensor.native_value - expected_value) < 1e-4

# --- Edge Case Tests ---

def test_edge_case_empty_data(mock_coordinator, mock_entry):
    mock_coordinator.data = mock_prices([])
    sensor = create_sensor(mock_coordinator, mock_entry, 50.0, "50% price low")
    assert sensor.native_value is None

def test_edge_case_single_data_point(mock_coordinator, mock_entry):
    prices = [{"date": {"current": True, "full": "2024-01-01 00:00"}, "price": 10.0}]
    mock_coordinator.data = mock_prices(prices)
    sensor = create_sensor(mock_coordinator, mock_entry, 50.0, "50% price low")
    assert sensor.native_value == 10.0

def test_edge_case_missing_current_flag(mock_coordinator, mock_entry):
    prices = [
        {"date": {"current": False, "full": "2024-01-01 00:00"}, "price": 1.0},
        {"date": {"current": False, "full": "2024-01-01 01:00"}, "price": 2.0},
    ]
    mock_coordinator.data = mock_prices(prices)
    sensor = create_sensor(mock_coordinator, mock_entry, 50.0, "50% price low")
    assert sensor.native_value is None # Should return None if no price is marked current

def test_edge_case_malformed_dates_empty_day_prices(mock_coordinator, mock_entry):
    # Prices exist, but none match the current day
    prices = [
        {"date": {"current": True, "full": "2024-01-02 00:00"}, "price": 1.0}, # Current date is Jan 1
        {"date": {"current": False, "full": "2024-01-01 01:00"}, "price": 2.0},
    ]
    mock_coordinator.data = mock_prices(prices)
    sensor = create_sensor(mock_coordinator, mock_entry, 50.0, "50% price low")
    assert sensor.native_value is None # Should return None as no prices are found for the current day (Jan 1)

def test_edge_case_only_one_price_in_day(mock_coordinator, mock_entry):
    prices = [
        {"date": {"current": True, "full": "2024-01-01 00:00"}, "price": 5.0},
        {"date": {"current": False, "full": "2024-01-02 00:00"}, "price": 10.0},
    ]
    mock_coordinator.data = mock_prices(prices)
    # Should handle gracefully by returning the single price
    sensor = create_sensor(mock_coordinator, mock_entry, 50.0, "50% price low")
    assert sensor.native_value == 5.0

# --- Configuration Integration Test (Phase 2 requirement) ---

def test_configuration_integration_multiple_percentiles(mock_coordinator, mock_entry):
    # Config entry specifies multiple percentiles
    percentiles_config = [0.05, 0.5, 0.95]
    config_entry_multi = MockConfigEntry({**mock_entry.data, CONF_PERCENTILES: percentiles_config})
    
    # Mock prices that support all calculations
    prices = [
        {"date": {"current": True, "full": "2024-01-01 00:00"}, "price": 1.0},
        {"date": {"current": False, "full": "2024-01-01 01:00"}, "price": 2.0},
        {"date": {"current": False, "full": "2024-01-01 02:00"}, "price": 3.0},
        {"date": {"current": False, "full": "2024-01-01 03:00"}, "price": 4.0},
        {"date": {"current": False, "full": "2024-01-01 04:00"}, "price": 5.0},
    ]
    mock_coordinator.data = mock_prices(prices)
    
    # Simulate the sensor creation loop from async_setup_entry
    sensors: list[PureEnergyPercentileSensor] = []
    for percentile in percentiles_config:
        name = f"{int(percentile * 100)}% price low"
        sensor = create_sensor(mock_coordinator, config_entry_multi, percentile, name)
        sensors.append(sensor)
    
    # Assert that the correct number of sensors were created
    assert len(sensors) == 3

    # Verify one sensor's value (e.g., 50th percentile)
    sensor_50 = sensors[1] 
    assert sensor_50.native_value == 3.0

    # Verify another sensor's value (e.g., 95th percentile - closest to 5.0)
    sensor_95 = sensors[2]
    # Index for 95% (0.95 * 4 = 3.8): low=3 (4.0), high=4 (5.0). interpolation=0.8. 4.0*(0.2) + 5.0*(0.8) = 0.8 + 4.0 = 4.8
    expected_95 = 4.8
    assert abs(sensor_95.native_value - expected_95) < 1e-4