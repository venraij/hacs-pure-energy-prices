"""Tests that current-hour price sensors update their state on the hour."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.pure_energy_prices.sensor import (
    PureEnergiePriceSensor,
    PureEnergieRawPriceSensor,
)


@pytest.mark.parametrize("sensor_class", [PureEnergiePriceSensor, PureEnergieRawPriceSensor])
async def test_registers_hourly_state_update(sensor_class):
    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = sensor_class(MagicMock(), entry)
    sensor.hass = MagicMock()

    with patch.object(
        CoordinatorEntity, "async_added_to_hass", AsyncMock()
    ), patch(
        "custom_components.pure_energy_prices.sensor.async_track_time_change"
    ) as track:
        await sensor.async_added_to_hass()

    track.assert_called_once_with(
        sensor.hass, sensor._async_hour_changed, minute=0, second=0
    )


@pytest.mark.parametrize("sensor_class", [PureEnergiePriceSensor, PureEnergieRawPriceSensor])
def test_hour_change_writes_state(sensor_class):
    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = sensor_class(MagicMock(), entry)

    with patch.object(sensor, "async_write_ha_state") as write:
        sensor._async_hour_changed(None)

    write.assert_called_once()
