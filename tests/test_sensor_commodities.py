"""Tests for sensor commodity creation and configuration."""
import pytest
from unittest.mock import MagicMock

from custom_components.pure_energy_prices.sensor import async_setup_entry
from custom_components.pure_energy_prices.const import (
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
    CONF_SOLAR_PANELS,
    DEFAULT_SCAN_INTERVAL,
    UNIT_KWH,
    UNIT_M3,
)


@pytest.mark.asyncio
async def test_electricity_import_sensor_created_by_default(mock_hass, entry_with_electricity):
    """Test that electricity import sensor is created by default."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_electricity, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    # Should include raw import sensor too (6 total now)
    assert len(call_args) == 6
    entity = call_args[0]
    assert "test_entry_id_electricity" in entity.unique_id
    assert "import" in entity.unique_id


@pytest.mark.asyncio
async def test_gas_import_sensor_created_when_gas_checked(mock_hass, entry_with_gas):
    """Test that gas import sensor is created when gas is checked."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_gas, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    # import(1+4+1raw) + gas(1+4) = 11 sensors
    assert len(call_args) == 11
    # Gas import sensor should be at index 5 (after electricity: import + 4 pct)
    gas_sensor = call_args[6]
    assert "test_entry_id_gas" in gas_sensor.unique_id
    assert "import" in gas_sensor.unique_id


@pytest.mark.asyncio
async def test_gas_import_sensor_not_created_when_gas_not_checked(mock_hass, entry_with_electricity):
    """Test that gas import sensor is not created when gas is not checked."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_electricity, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    # Should only have electricity import sensors (6 now with raw)
    assert len(call_args) == 6
    assert not any("pure_energie_gas" in e.unique_id for e in call_args)


@pytest.mark.asyncio
async def test_electricity_export_sensor_created_when_solar_panels(mock_hass, entry_with_solar):
    """Test that electricity export sensor is created when solar panels are checked."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_solar, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    # import(1+4+1raw) + export(1+4+1raw) = 12
    assert len(call_args) == 12
    export_sensor = call_args[6]
    assert "redelivery" in export_sensor.unique_id
    assert "export" in export_sensor.unique_id


@pytest.mark.asyncio
async def test_electricity_export_sensor_not_created_when_solar_panels_false(mock_hass, entry_with_electricity):
    """Test that electricity export sensor is not created when solar panels are not checked."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_electricity, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    # import(0) + pct(1-4) + raw(5) = 6 sensors
    assert len(call_args) == 6
    assert not any("export" in e.unique_id for e in call_args)


@pytest.mark.asyncio
async def test_gas_export_sensor_not_created(mock_hass, entry_with_gas):
    """Test that gas export sensor is never created (gas has no export)."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_gas, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert not any("export" in e.unique_id for e in call_args)


@pytest.mark.asyncio
async def test_unit_of_measurement_electricity(mock_hass, entry_with_electricity):
    """Test that electricity sensors have correct unit of measurement."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_electricity, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    for e in call_args:
        if "pure_energie_electricity" in e.unique_id:
            assert e._commodity == "electricity"
            assert e.native_unit_of_measurement == "kWh"


@pytest.mark.asyncio
async def test_unit_of_measurement_gas(mock_hass, entry_with_gas):
    """Test that gas sensors have correct unit of measurement."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_gas, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    gas_sensors = [e for e in call_args if "pure_energie_gas" in e.unique_id]
    for s in gas_sensors:
        assert s.native_unit_of_measurement == "m³"


@pytest.mark.asyncio
async def test_percentile_sensors_created_for_electricity(mock_hass, entry_with_gas):
    """Test that percentile sensors are created for electricity."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_gas, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    pct_sensors = [e for e in call_args if "percentile" in e.unique_id]
    # Electricity import percentiles + gas import percentiles
    assert len(pct_sensors) == 8
