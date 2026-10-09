"""Tests for multi-percentile sensor creation in sensor.py async_setup_entry."""
import pytest
from unittest.mock import MagicMock

from custom_components.pure_energy_prices.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_electricity_import_only(mock_hass, entry_with_electricity):
    """Electricity only (no solar, no percentiles -> defaults to 4).
    Result: 1 main import + 4 percentile + 1 raw import = 6 sensors."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_electricity, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 6


@pytest.mark.asyncio
async def test_electricity_with_solar_and_percentiles(mock_hass, entry_with_solar):
    """Electricity + solar + percentiles.
    Result: import(1+4+1raw) + export(1+4+1raw) = 12 sensors."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_solar, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 12


@pytest.mark.asyncio
async def test_gas_import(mock_hass, entry_with_gas):
    """Gas enabled: import(1+4+1raw) + gas(1+4) = 11 sensors."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_with_gas, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 11


@pytest.mark.asyncio
async def test_no_percentiles_uses_defaults(mock_hass, entry_no_percentiles):
    """Missing percentiles -> DEFAULT_PERCENTILES (4 values) -> 6 sensors."""
    add_entities_mock = MagicMock()
    await async_setup_entry(mock_hass, entry_no_percentiles, add_entities_mock)
    call_args = add_entities_mock.call_args[0][0]
    assert len(call_args) == 6
