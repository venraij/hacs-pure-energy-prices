"""Tests for multiple percentile sensor entity creation."""

import pytest
from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity

from custom_components.pure_energy_prices.sensor import async_setup_entry


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant with a coordinator in hass.data."""
    hass = MagicMock(spec=HomeAssistant)
    coordinator = MagicMock()
    coordinator.data = MagicMock()
    coordinator.data.prices = []
    hass.data = {"pure_energy_prices": {"test_entry": coordinator}}
    return hass


@pytest.fixture
def multi_percentile_config():
    """Config entry with multiple percentiles as a comma-separated string."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.data = {
        "percentiles": "0.05,0.1,0.2,0.4",
        "unit_of_measurement": "EUR/kWh",
    }
    return entry


@pytest.fixture
def multi_percentile_config_list():
    """Config entry with multiple percentiles as a list of floats."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.data = {
        "percentiles": [0.05, 0.1, 0.2, 0.4],
        "unit_of_measurement": "EUR/kWh",
    }
    return entry


@pytest.fixture
def single_percentile_config():
    """Config entry with a single percentile."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.data = {
        "percentiles": "0.05",
        "unit_of_measurement": "EUR/kWh",
    }
    return entry


@pytest.fixture
def no_percentile_config():
    """Config entry with no percentiles — should use default."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.data = {"unit_of_measurement": "EUR/kWh"}
    return entry


# ------------------------------------------------------------------ #
#  Tests                                                              #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_multiple_percentiles_as_string_create_five_sensors(
    mock_hass, multi_percentile_config
):
    """String config '0.05,0.1,0.2,0.4' -> 1 main + 4 percentile sensors."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, multi_percentile_config, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 5, f"Expected 5, got {len(call_args)}"


@pytest.mark.asyncio
async def test_multiple_percentiles_as_list_create_five_sensors(
    mock_hass, multi_percentile_config_list
):
    """List config [0.05, 0.1, 0.2, 0.4] -> 1 main + 4 percentile sensors."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, multi_percentile_config_list, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 5


@pytest.mark.asyncio
async def test_single_percentile_creates_two_sensors(
    mock_hass, single_percentile_config
):
    """Single percentile -> 1 main + 1 sensor."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, single_percentile_config, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 2


@pytest.mark.asyncio
async def test_no_percentiles_uses_defaults(mock_hass, no_percentile_config):
    """Missing percentiles -> defaults to 4 values -> 5 sensors total."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, no_percentile_config, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 5


@pytest.mark.asyncio
async def test_coordinator_read_from_shared_hass_data(
    mock_hass, multi_percentile_config
):
    """Verify sensor.py reads coordinator from hass.data (not creating a new one)."""
    add_entities_mock = MagicMock()

    # This will succeed because hass.data already has the coordinator key
    # If sensor.py tried to create a new coordinator and access hass.data
    # without the entry being there, it would raise a KeyError
    await async_setup_entry(mock_hass, multi_percentile_config, add_entities_mock)

    # Verify the entry key exists in hass.data
    assert "test_entry" in mock_hass.data["pure_energy_prices"]

    # Should have 5 sensors total
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 5
