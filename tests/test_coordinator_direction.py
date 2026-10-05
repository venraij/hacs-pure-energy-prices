"""Tests for coordinator direction-based price adjustments."""

import pytest
from unittest.mock import MagicMock, patch

from custom_components.pure_energy_prices.const import (
    CONF_ADDED_COSTS,
    CONF_RETURN_COSTS,
)
from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator


class TestCoordinatorCostAdjustments:
    """Test that cost adjustments are applied only to today's prices."""

    def _make_coordinator(self, direction="import"):
        """Create a coordinator without HA setup."""
        entry = MagicMock()
        entry.data = {CONF_ADDED_COSTS: 0.05, CONF_RETURN_COSTS: 0.03}
        with patch.object(
            PureEnergyCoordinator,
            "__init__",
            lambda self, *args, **kwargs: None,
        ):
            coordinator = PureEnergyCoordinator.__new__(PureEnergyCoordinator)
            coordinator._entry = entry
            coordinator._element_id = 11480
            coordinator._commodity = "electricity"
            coordinator._direction = direction
            coordinator.data = MagicMock()
            coordinator.data.prices = []
            return coordinator

    def test_import_applies_added_costs_for_today(self):
        """Import direction should add config CONF_ADDED_COSTS for today's prices."""
        coordinator = self._make_coordinator(direction="import")
        prices = [{"price": 0.20}]  # No date field = treated as today
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == pytest.approx(0.25)

    def test_import_skips_adjustments_for_next_day(self):
        """Future prices should be adjusted."""
        coordinator = self._make_coordinator(direction="import")
        from datetime import datetime, timedelta, timezone

        tomorrow = datetime.now(tz=timezone.utc) + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d") + "T00:00"

        prices = [
            {"price": 0.20},  # Today: adjusted
            {"price": 0.25, "date": {"full": tomorrow_str}},  # Tomorrow: adjusted
        ]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == pytest.approx(0.25)
        assert adjusted[1]["price"] == pytest.approx(0.30)

    def test_export_applies_return_costs_for_today(self):
        """Export direction should add config CONF_RETURN_COSTS for today's prices."""
        coordinator = self._make_coordinator(direction="export")
        prices = [{"price": 0.20}]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == pytest.approx(0.23)

    def test_export_skips_adjustments_for_next_day(self):
        """Future prices should be adjusted."""
        coordinator = self._make_coordinator(direction="export")
        from datetime import datetime, timedelta, timezone

        tomorrow = datetime.now(tz=timezone.utc) + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d") + "T00:00"

        prices = [
            {"price": 0.25},  # Today: adjusted
            {"price": 0.30, "date": {"full": tomorrow_str}},  # Tomorrow: adjusted
        ]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == pytest.approx(0.28)
        assert adjusted[1]["price"] == pytest.approx(0.33)

    def test_two_days_ahead_prices_skip_adjustments(self):
        """Prices for dates more than 1 day ahead are also adjusted."""
        coordinator = self._make_coordinator(direction="import")
        from datetime import datetime, timedelta, timezone

        two_days = datetime.now(tz=timezone.utc) + timedelta(days=2)
        two_days_str = two_days.strftime("%Y-%m-%d") + "T00:00"

        prices = [
            {"price": 0.20},  # Today: adjusted
            {"price": 0.22, "date": {"full": two_days_str}},  # Day after tomorrow: adjusted
        ]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == pytest.approx(0.25)
        assert adjusted[1]["price"] == pytest.approx(0.27)

    def test_past_day_prices_get_adjustments(self):
        """Past-day prices should also get adjustments."""
        coordinator = self._make_coordinator(direction="import")
        from datetime import datetime, timedelta, timezone

        yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d") + "T00:00"

        prices = [{"price": 0.20, "date": {"full": yesterday_str}}]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == pytest.approx(0.25)

    def test_record_without_date_field_gets_adjustments(self):
        """Records without a date field are treated as today."""
        coordinator = self._make_coordinator(direction="import")
        prices = [{"price": 0.25}]
        adjusted = coordinator._apply_cost_adjustments(prices)
        assert adjusted[0]["price"] == pytest.approx(0.30)

    def test_get_record_date_nested_structure(self):
        """Test _get_record_date with nested date.full structure."""
        coordinator = self._make_coordinator()
        record = {"date": {"full": "2026-10-01T12:00"}}
        result = coordinator._get_record_date(record)
        assert result is not None
        assert str(result) == "2026-10-01"

    def test_get_record_date_top_level_full(self):
        """Test _get_record_date with top-level full field."""
        coordinator = self._make_coordinator()
        record = {"full": "2026-10-01T12:00"}
        result = coordinator._get_record_date(record)
        assert result is not None
        assert str(result) == "2026-10-01"

    def test_get_record_date_no_date_field(self):
        """Test _get_record_date returns None when no date field."""
        coordinator = self._make_coordinator()
        record = {"price": 0.25}
        result = coordinator._get_record_date(record)
        assert result is None

    def test_get_record_date_invalid_date(self):
        """Test _get_record_date handles invalid date gracefully."""
        coordinator = self._make_coordinator()
        record = {"date": {"full": "not-a-date"}}
        result = coordinator._get_record_date(record)
        assert result is None
