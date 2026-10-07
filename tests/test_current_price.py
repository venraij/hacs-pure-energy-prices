"""Tests for selecting the current hour's price and refreshing the sensors."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator
from custom_components.pure_energy_prices.sensor import (
    PureEnergiePercentileSensor,
    PureEnergiePriceSensor,
    get_current_price_record,
)
from tests.fixtures.pure_energie_data import prices as FIXTURE_PRICES

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def _make_sensor(prices):
    coordinator = MagicMock()
    coordinator.data = MagicMock()
    coordinator.data.prices = prices
    entry = MagicMock()
    entry.entry_id = "test_entry"
    return PureEnergiePriceSensor(coordinator, entry)


class TestGetCurrentPriceRecord:
    """Test picking the record for the current local hour."""

    def test_returns_record_for_current_hour(self):
        now = datetime(2026, 9, 16, 17, 25, tzinfo=AMSTERDAM)
        record = get_current_price_record(FIXTURE_PRICES, now)
        assert record["date"]["full"] == "2026-09-16 17:00"

    def test_returns_none_when_hour_not_in_data(self):
        now = datetime(2026, 9, 18, 12, 0, tzinfo=AMSTERDAM)
        assert get_current_price_record(FIXTURE_PRICES, now) is None

    def test_ignores_records_without_date(self):
        now = datetime(2026, 9, 16, 0, 0, tzinfo=AMSTERDAM)
        assert get_current_price_record([{"price": 0.1}], now) is None


class TestPriceSensorNativeValue:
    """Test that the price sensor reports the current hour, not the first."""

    def test_native_value_is_current_hour_price(self):
        sensor = _make_sensor(FIXTURE_PRICES)
        now = datetime(2026, 9, 16, 17, 25, tzinfo=AMSTERDAM)
        expected = next(
            p["price"] for p in FIXTURE_PRICES if p["date"]["full"] == "2026-09-16 17:00"
        )
        with patch(
            "custom_components.pure_energy_prices.sensor.dt_util.now",
            return_value=now,
        ):
            assert sensor.native_value == round(expected, 2)

    def test_native_value_changes_with_the_hour(self):
        sensor = _make_sensor(FIXTURE_PRICES)
        values = []
        for hour in (0, 17):
            now = datetime(2026, 9, 16, hour, 0, tzinfo=AMSTERDAM)
            with patch(
                "custom_components.pure_energy_prices.sensor.dt_util.now",
                return_value=now,
            ):
                values.append(sensor.native_value)
        assert values[0] != values[1]

    def test_falls_back_to_api_current_when_hour_missing(self):
        sensor = _make_sensor(FIXTURE_PRICES)
        now = datetime(2026, 9, 20, 12, 0, tzinfo=AMSTERDAM)
        expected = next(p["price"] for p in FIXTURE_PRICES if p["date"]["current"])
        with patch(
            "custom_components.pure_energy_prices.sensor.dt_util.now",
            return_value=now,
        ):
            assert sensor.native_value == round(expected, 2)

    def test_current_hour_wins_over_stale_api_current_flag(self):
        """After an hour passes, the API's `current` flag from the last fetch is stale."""
        sensor = _make_sensor(FIXTURE_PRICES)
        flagged = next(p for p in FIXTURE_PRICES if p["date"]["current"])
        other = next(
            p for p in FIXTURE_PRICES
            if not p["date"]["current"] and round(p["price"], 2) != round(flagged["price"], 2)
        )
        hour = int(other["date"]["hour"][:2])
        now = datetime(2026, 9, 16, hour, 30, tzinfo=AMSTERDAM)
        with patch(
            "custom_components.pure_energy_prices.sensor.dt_util.now",
            return_value=now,
        ):
            assert sensor.native_value == round(other["price"], 2)


class TestSensorsFollowCoordinator:
    """Sensors must listen to the coordinator, otherwise it never refreshes."""

    def test_price_sensor_is_coordinator_entity(self):
        assert issubclass(PureEnergiePriceSensor, CoordinatorEntity)

    def test_percentile_sensor_is_coordinator_entity(self):
        assert issubclass(PureEnergiePercentileSensor, CoordinatorEntity)


class TestCoordinatorUsesLocalTime:
    """The API expects local time for the `current` parameter."""

    @pytest.fixture
    def coordinator(self):
        with patch.object(PureEnergyCoordinator, "__init__", lambda self, *a, **k: None):
            coordinator = PureEnergyCoordinator.__new__(PureEnergyCoordinator)
        coordinator._commodity = "electricity"
        coordinator._direction = "import"
        coordinator.data = MagicMock()
        return coordinator

    async def test_fetch_uses_local_time(self, coordinator):
        now = datetime(2026, 10, 5, 0, 30, tzinfo=AMSTERDAM)
        coordinator._fetch_prices = AsyncMock(return_value=[])
        with patch(
            "custom_components.pure_energy_prices.coordinator.dt_util.now",
            return_value=now,
        ):
            await coordinator._async_update_data()
        first_call_dt = coordinator._fetch_prices.await_args_list[0].args[0]
        assert coordinator._build_current_param(first_call_dt) == "2026-10-05 00:30"
