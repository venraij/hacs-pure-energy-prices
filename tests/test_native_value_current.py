"""Tests for PureEnergiePriceSensor native_value — current hour fix."""

import json
import pytest
from unittest.mock import MagicMock, PropertyMock
from custom_components.pure_energy_prices.sensor import PureEnergiePriceSensor


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with real fixture data."""
    coordinator = MagicMock()

    with open("tests/fixtures/pure_energie_real_data.json") as f:
        fixture = json.load(f)

    # Wrap the fixture data as a simple object with a .prices attribute
    class FakeData:
        def __init__(self, prices):
            self.prices = prices

    coordinator.data = FakeData(fixture["prices"])
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Minimal mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_001"
    return entry


class TestNativeValueCurrentHour:
    """Verify native_value returns the price for the current hour, not data[0]."""

    def test_native_value_returns_current_hour_price(self, mock_coordinator, mock_config_entry):
        """native_value should pick the entry where date.current is true."""
        sensor = PureEnergiePriceSensor(mock_coordinator, mock_config_entry)
        value = sensor.native_value
        # The fixture has current:true for 18:00 slot, price=0.3904549
        assert value == pytest.approx(0.39)

    def test_native_value_falls_back_to_first_when_no_current(self, mock_config_entry):
        """If no entry is marked current, fall back to data[0]."""
        coordinator = MagicMock()
        # Provide prices with no date.current field
        class FakeData:
            def __init__(self):
                self.prices = [{"price": 0.12345}]
        coordinator.data = FakeData()
        sensor = PureEnergiePriceSensor(coordinator, mock_config_entry)
        value = sensor.native_value
        assert value == pytest.approx(0.12)

    def test_native_value_empty_data(self, mock_config_entry):
        """With no data, native_value should return None."""
        coordinator = MagicMock()
        coordinator.data = None
        sensor = PureEnergiePriceSensor(coordinator, mock_config_entry)
        assert sensor.native_value is None

    def test_native_value_empty_list(self, mock_config_entry):
        """With an empty list, native_value should return None."""
        coordinator = MagicMock()
        class FakeData:
            prices = []
        coordinator.data = FakeData()
        sensor = PureEnergiePriceSensor(coordinator, mock_config_entry)
        assert sensor.native_value is None

    def test_native_value_no_date_dict(self, mock_config_entry):
        """If date is not a dict, skip and use fallback to first entry."""
        coordinator = MagicMock()
        class FakeData:
            prices = [{"price": 0.42, "date": "invalid"}, {"price": 0.99}]
        coordinator.data = FakeData()
        sensor = PureEnergiePriceSensor(coordinator, mock_config_entry)
        value = sensor.native_value
        # First entry has no dict date, so it should fall through and use first
        assert value == pytest.approx(0.42)
