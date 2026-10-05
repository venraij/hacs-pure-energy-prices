"""Tests for export commodity fix (redelivery) and return cost subtraction."""

import pytest
from unittest.mock import MagicMock, patch

from custom_components.pure_energy_prices.const import CONF_COMMODITY_ELECTRICITY, CONF_RETURN_COSTS
from custom_components.pure_energy_prices.const import CONF_COMMODITY_REDELIVERY
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


class TestExportUsesRedelivery:
    """Export should use commodity 'redelivery', not 'electricity'."""

    def _make_coordinator(self, direction="export", commodity=CONF_COMMODITY_REDELIVERY):
        entry = MagicMock()
        entry.data = {CONF_RETURN_COSTS: 0.03}
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

    def test_export_subtracts_return_costs(self):
        """Export prices should have return costs SUBTRACTED (not added)."""
        coordinator = self._make_coordinator(direction="export")
        coordinator._commodity = "redelivery"
        prices = [{"price": 0.15}]  # API price: 0.15
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.12)  # 0.15 - 0.03

    def test_export_futures_adjusted_not_skipped(self):
        """Future export prices (non-zero) are NOT skipped — they still get adjustments."""
        from datetime import datetime, timedelta, timezone

        coordinator = self._make_coordinator(direction="export")
        coordinator._commodity = "redelivery"
        tomorrow = datetime.now(tz=timezone.utc) + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%dT00:00")

        prices = [{"price": 0.25, "date": {"full": tomorrow_str}}]
        result = coordinator._apply_cost_adjustments(prices)
        # Tomorrow's price IS adjusted (subtracted), not skipped
        assert result[0]["price"] == pytest.approx(0.22)  # 0.25 - 0.03

    def test_export_zeros_future_price_skipped(self):
        """Future prices with price==0 are skipped."""
        from datetime import datetime, timedelta, timezone

        coordinator = self._make_coordinator(direction="export")
        coordinator._commodity = "redelivery"
        tomorrow = datetime.now(tz=timezone.utc) + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%dT00:00")

        prices = [{"price": 0.0, "date": {"full": tomorrow_str}}]
        result = coordinator._apply_cost_adjustments(prices)
        # Zero-price future records are skipped, result should be empty
        assert result == []

    def test_import_still_adds_costs(self):
        """Import direction should still ADD added_costs (unchanged behavior)."""
        coordinator = self._make_coordinator(direction="import", commodity=CONF_COMMODITY_ELECTRICITY)
        coordinator._entry.data["added_costs"] = 0.02
        prices = [{"price": 0.10}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(0.12)  # 0.10 + 0.02
