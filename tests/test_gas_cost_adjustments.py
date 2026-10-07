"""Tests for gas price handling — no added/return costs should apply to gas."""

import pytest
from unittest.mock import MagicMock, patch

from custom_components.pure_energy_prices.const import (
    CONF_COMMODITY_GAS,
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_REDELIVERY,
    CONF_ADDED_COSTS,
    CONF_RETURN_COSTS,
)
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


class TestGasNoAddedCosts:
    """Gas should never have electricity added costs applied."""

    def _make_coordinator(self, direction="import", commodity=CONF_COMMODITY_GAS):
        entry = MagicMock()
        entry.data = {CONF_ADDED_COSTS: 0.05, CONF_RETURN_COSTS: 0.03}
        with patch.object(
            PureEnergyCoordinator,
            "__init__",
            lambda self, *args, **kwargs: None,
        ):
            coordinator = PureEnergyCoordinator.__new__(PureEnergyCoordinator)
            coordinator._entry = entry
            coordinator._direction = direction
            coordinator._commodity = commodity
            return coordinator

    def test_gas_import_no_added_costs(self):
        """Gas import should NOT have added costs applied."""
        coordinator = self._make_coordinator(direction="import", commodity=CONF_COMMODITY_GAS)
        prices = [{"price": 0.85}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.85)  # unchanged

    def test_gas_import_no_added_costs_high_added(self):
        """Even with high added_costs, gas price remains unchanged."""
        coordinator = self._make_coordinator(direction="import", commodity=CONF_COMMODITY_GAS)
        coordinator._entry.data[CONF_ADDED_COSTS] = 0.10
        prices = [{"price": 0.85}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.85)

    def test_gas_export_no_return_costs(self):
        """Gas export should NOT have return costs subtracted."""
        coordinator = self._make_coordinator(direction="export", commodity=CONF_COMMODITY_GAS)
        prices = [{"price": 0.15}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.15)  # unchanged

    def test_gas_export_no_return_costs_high_return(self):
        """Even with high return_costs, gas export price remains unchanged."""
        coordinator = self._make_coordinator(direction="export", commodity=CONF_COMMODITY_GAS)
        coordinator._entry.data[CONF_RETURN_COSTS] = 0.05
        prices = [{"price": 0.15}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.15)

    def test_gas_multiple_prices_unchanged(self):
        """All gas prices should be returned unchanged."""
        coordinator = self._make_coordinator(direction="import", commodity=CONF_COMMODITY_GAS)
        coordinator._entry.data[CONF_ADDED_COSTS] = 0.05
        prices = [
            {"price": 0.80},
            {"price": 0.85},
            {"price": 0.90},
        ]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.80)
        assert result[1]["price"] == pytest.approx(0.85)
        assert result[2]["price"] == pytest.approx(0.90)


class TestElectricityUnaffected:
    """Ensure the gas fix doesn't break electricity behavior."""

    def _make_coordinator(self, direction="import", commodity=CONF_COMMODITY_ELECTRICITY):
        entry = MagicMock()
        entry.data = {CONF_ADDED_COSTS: 0.02, CONF_RETURN_COSTS: 0.03}
        with patch.object(
            PureEnergyCoordinator,
            "__init__",
            lambda self, *args, **kwargs: None,
        ):
            coordinator = PureEnergyCoordinator.__new__(PureEnergyCoordinator)
            coordinator._entry = entry
            coordinator._direction = direction
            coordinator._commodity = commodity
            return coordinator

    def test_electricity_import_still_adds_costs(self):
        """Electricity import should still ADD added_costs."""
        coordinator = self._make_coordinator(direction="import", commodity=CONF_COMMODITY_ELECTRICITY)
        prices = [{"price": 0.10}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.12)

    def test_redelivery_export_still_subtracts_costs(self):
        """Redelivery export should still SUBTRACT return_costs."""
        coordinator = self._make_coordinator(
            direction="export", commodity=CONF_COMMODITY_REDELIVERY
        )
        prices = [{"price": 0.15}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.12)  # 0.15 - 0.03
