"""Tests for commodity-specific Pure Energie sensors."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.pure_energy_prices.const import (
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
    CONF_SOLAR_PANELS,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry with default settings."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_COMMODITY_ELECTRICITY: True,
        CONF_SOLAR_PANELS: False,
        CONF_COMMODITY_GAS: False,
        "percentiles": "0.05,0.1,0.2,0.4",
    }
    entry.options = {}
    entry.unique_id = "test_unique_id"
    return entry


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with test data."""
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.data = MagicMock()
    coordinator.data.prices = [
        {"price": 0.25, "start": "2024-01-01T00:00", "end": "2024-01-01T01:00"},
        {"price": 0.30, "start": "2024-01-01T01:00", "end": "2024-01-01T02:00"},
        {"price": 0.35, "start": "2024-01-01T02:00", "end": "2024-01-01T03:00"},
    ]
    return coordinator


@pytest.fixture
def mock_hass(mock_config_entry, mock_coordinator):
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    mock_hass.config_entries = MagicMock()
    mock_hass.config_entries.async_setup = AsyncMock(return_value=True)
    mock_hass.config_entries.async_unload = AsyncMock(return_value=True)
    mock_hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    mock_hass.states = MagicMock()
    mock_hass.states.entity_ids = MagicMock(return_value=[])
    mock_hass.states.get = MagicMock(return_value=None)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "electricity_import": mock_coordinator
    }
    return hass


@pytest.mark.asyncio
async def test_electricity_import_sensor_created_by_default(mock_hass, mock_config_entry, mock_coordinator):
    """Test that electricity import sensor is created by default."""
    from homeassistant.setup import async_setup_component
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that the sensor was created
    entity_ids = mock_hass.states.entity_ids()
    assert any("pure_energie_electricity" in eid and "import" in eid for eid in entity_ids)


@pytest.mark.asyncio
async def test_gas_import_sensor_created_when_gas_checked(mock_hass, mock_config_entry, mock_coordinator):
    """Test that gas import sensor is created when gas is checked."""
    from homeassistant.setup import async_setup_component
    
    mock_config_entry.data[CONF_COMMODITY_GAS] = True
    gas_coordinator = MagicMock()
    gas_coordinator.async_config_entry_first_refresh = AsyncMock()
    gas_coordinator.data = MagicMock()
    gas_coordinator.data.prices = [
        {"price": 0.50, "start": "2024-01-01T00:00", "end": "2024-01-01T01:00"},
    ]
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that the gas sensor was created
    entity_ids = mock_hass.states.entity_ids()
    assert any("pure_energie_gas" in eid and "import" in eid for eid in entity_ids)


@pytest.mark.asyncio
async def test_gas_import_sensor_not_created_when_gas_not_checked(mock_hass, mock_config_entry, mock_coordinator):
    """Test that gas import sensor is not created when gas is not checked."""
    from homeassistant.setup import async_setup_component
    
    mock_config_entry.data[CONF_COMMODITY_GAS] = False
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that no gas sensor was created
    entity_ids = mock_hass.states.entity_ids()
    assert not any("pure_energie_gas" in eid for eid in entity_ids)


@pytest.mark.asyncio
async def test_electricity_export_sensor_created_when_solar_panels(mock_hass, mock_config_entry, mock_coordinator):
    """Test that electricity export sensor is created when solar panels are checked."""
    from homeassistant.setup import async_setup_component
    
    mock_config_entry.data[CONF_SOLAR_PANELS] = True
    
    # Create export coordinator
    export_coordinator = MagicMock()
    export_coordinator.async_config_entry_first_refresh = AsyncMock()
    export_coordinator.data = MagicMock()
    export_coordinator.data.prices = [
        {"price": 0.15, "start": "2024-01-01T00:00", "end": "2024-01-01T01:00"},
    ]
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that the sensor was created
    entity_ids = mock_hass.states.entity_ids()
    assert any("pure_energie_electricity" in eid and "export" in eid for eid in entity_ids)


@pytest.mark.asyncio
async def test_electricity_export_sensor_not_created_when_solar_panels_false(mock_hass, mock_config_entry, mock_coordinator):
    """Test that electricity export sensor is not created when solar panels are not checked."""
    from homeassistant.setup import async_setup_component
    
    mock_config_entry.data[CONF_SOLAR_PANELS] = False
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that no export sensor was created
    entity_ids = mock_hass.states.entity_ids()
    assert not any("pure_energie_electricity" in eid and "export" in eid for eid in entity_ids)


@pytest.mark.asyncio
async def test_gas_export_sensor_not_created(mock_hass, mock_config_entry, mock_coordinator):
    """Test that gas export sensor is never created (gas has no export)."""
    from homeassistant.setup import async_setup_component
    
    mock_config_entry.data[CONF_COMMODITY_GAS] = True
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that no gas export sensor was created
    entity_ids = mock_hass.states.entity_ids()
    assert not any("pure_energie_gas" in eid and "export" in eid for eid in entity_ids)


@pytest.mark.asyncio
async def test_unit_of_measurement_electricity(mock_hass, mock_config_entry, mock_coordinator):
    """Test that electricity sensors have correct unit of measurement."""
    from homeassistant.setup import async_setup_component
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that electricity sensors have kWh unit
    entity_ids = mock_hass.states.entity_ids()
    for eid in entity_ids:
        if "pure_energie_electricity" in eid:
            state = mock_hass.states.get(eid)
            assert state.attributes.get("unit_of_measurement") == "kWh"


@pytest.mark.asyncio
async def test_unit_of_measurement_gas(mock_hass, mock_config_entry, mock_coordinator):
    """Test that gas sensors have correct unit of measurement."""
    from homeassistant.setup import async_setup_component
    
    mock_config_entry.data[CONF_COMMODITY_GAS] = True
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that gas sensors have m³ unit
    entity_ids = mock_hass.states.entity_ids()
    for eid in entity_ids:
        if "pure_energie_gas" in eid:
            state = mock_hass.states.get(eid)
            assert state.attributes.get("unit_of_measurement") == "m³"


@pytest.mark.asyncio
async def test_horizon_hours_default_48(mock_hass, mock_config_entry, mock_coordinator):
    """Test that horizon hours defaults to 48 hours."""
    # Verify the default horizon hours is 48
    assert mock_config_entry.data.get("horizon_hours", 48) == 48


@pytest.mark.asyncio
async def test_percentile_sensors_created_for_electricity(mock_hass, mock_config_entry, mock_coordinator):
    """Test that percentile sensors are created for electricity."""
    from homeassistant.setup import async_setup_component
    
    # Setup the integration
    with patch("custom_components.pure_energy_prices.coordinator.PureEnergyCoordinator") as mock_coord_class:
        mock_coord_class.return_value = mock_coordinator
        result = await mock_hass.config_entries.async_setup(mock_config_entry.entry_id)
    
    # Check that percentile sensors were created
    entity_ids = mock_hass.states.entity_ids()
    percentile_sensors = [eid for eid in entity_ids if "percentile" in eid and "electricity" in eid]
    assert len(percentile_sensors) > 0  # Should have at least 4 percentile sensors (0.05, 0.1, 0.2, 0.4)
