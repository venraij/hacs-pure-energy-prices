"""Tests for the PureEnergieRawPriceSensor class."""

import pytest
from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorStateClass

from custom_components.pure_energy_prices.sensor import PureEnergieRawPriceSensor


@pytest.fixture
def mock_raw_coordinator():
    """Create a mock coordinator with raw_prices data."""
    coord = MagicMock()
    coord.data = MagicMock()
    coord.data.raw_prices = [
        {"price": 0.12},
        {"price": 0.15},
        {"price": 0.10},
    ]
    return coord


@pytest.fixture
def mock_raw_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = {"unit_of_measurement": "\u20ac/kWh"}
    entry.entry_id = "test_entry"
    return entry


@pytest.fixture
def raw_import_sensor(mock_raw_coordinator, mock_raw_entry):
    """Create a raw import sensor instance."""
    return PureEnergieRawPriceSensor(
        mock_raw_coordinator,
        mock_raw_entry,
        commodity="electricity",
        direction="import",
        unit_of_measurement="\u20ac/kWh",
    )


def test_raw_sensor_creation(raw_import_sensor):
    """Test raw sensor creation."""
    assert raw_import_sensor._direction == "import"
    assert raw_import_sensor._commodity == "electricity"


def test_raw_sensor_unit_of_measurement(raw_import_sensor):
    """Test raw sensor unit of measurement."""
    assert raw_import_sensor.native_unit_of_measurement == "\u20ac/kWh"


def test_raw_sensor_state_class(raw_import_sensor):
    """Test raw sensor state class."""
    assert raw_import_sensor.state_class == SensorStateClass.MEASUREMENT


def test_raw_sensor_native_value_with_data(raw_import_sensor, mock_raw_coordinator):
    """Test raw sensor returns the current raw price."""
    mock_raw_coordinator.data.raw_prices = [
        {"price": 0.12},
        {"price": 0.15},
        {"price": 0.10},
    ]
    value = raw_import_sensor.native_value
    assert value is not None
    assert isinstance(value, float)
    # Without timestamp data, sensor falls back to first entry (0.12)
    assert round(value, 2) == 0.12


def test_raw_sensor_native_value_empty_data(raw_import_sensor):
    """Test raw sensor returns None when no raw data."""
    raw_import_sensor.coordinator.data.raw_prices = []
    value = raw_import_sensor.native_value
    assert value is None
