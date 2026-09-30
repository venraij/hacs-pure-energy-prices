"""Tests for coordinator direction-based price adjustment."""
import pytest
from unittest.mock import MagicMock, patch

from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


class TestCoordinatorPriceAdjustment:
    """Test that the coordinator applies cost adjustments correctly."""

    def _make_coordinator(self, entry_data, **kwargs):
        """Helper to create coordinator without HA setup."""
        entry = MagicMock()
        entry.data = dict(entry_data)
        with patch.object(PureEnergyCoordinator, "__init__", lambda self, *a, **k: None):
            coordinator = PureEnergyCoordinator.__new__(PureEnergyCoordinator)
            coordinator._entry = entry
            coordinator._element_id = kwargs.get("element_id")
            coordinator._commodity = kwargs.get("commodity")
            coordinator._direction = kwargs.get("direction", "import")
            coordinator.data = MagicMock()
            coordinator.data.prices = []
            return coordinator

    def test_import_direction_adds_added_costs(self):
        """Import direction should add CONF_ADDED_COSTS to each price."""
        coordinator = self._make_coordinator(
            {"added_costs": 0.05, "return_costs": 0.0},
            element_id=11480,
            commodity="electricity",
            direction="import",
        )
        prices = [
            {"price": 0.25},
            {"price": 0.30},
        ]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == 0.30  # 0.25 + 0.05
        assert adjusted[1]["price"] == 0.35  # 0.30 + 0.05

    def test_export_direction_subtracts_return_costs(self):
        """Export direction should subtract CONF_RETURN_COSTS from each price."""
        coordinator = self._make_coordinator(
            {"added_costs": 0.0, "return_costs": 0.03},
            element_id=11480,
            commodity="electricity",
            direction="export",
        )
        prices = [
            {"price": 0.25},
            {"price": 0.30},
        ]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == 0.28  # 0.25 + 0.03
        assert adjusted[1]["price"] == pytest.approx(0.33) # 0.30 + 0.03

    def test_return_costs_defaults_to_zero_when_not_set(self):
        """When CONF_RETURN_COSTS is not in entry data, default to 0.0."""
        coordinator = self._make_coordinator(
            {"added_costs": 0.05},
            element_id=11480,
            commodity="electricity",
            direction="export",
        )
        prices = [{"price": 0.25}]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == 0.25  # no subtraction (default 0.0)

    def test_added_costs_defaults_to_zero_when_not_set(self):
        """When CONF_ADDED_COSTS is not in entry data, default to 0.0."""
        coordinator = self._make_coordinator(
            {"return_costs": 0.03},
            element_id=11480,
            commodity="electricity",
            direction="import",
        )
        prices = [{"price": 0.25}]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == 0.25  # no addition (default 0.0)
