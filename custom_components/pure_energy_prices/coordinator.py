"""Coordinator for Pure Energie Prices integration."""

from __future__ import annotations

import json
import logging
from datetime import datetime, date, timedelta, timezone

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.pure_energy_prices.const import (
    CONF_ADDED_COSTS,
    CONF_BASE_URL,
    CONF_BUSINESS,
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
    CONF_DOUBLE_METER,
    CONF_GAS_ELEMENT_ID,
    CONF_RETURN_COSTS,
    CONF_SCAN_INTERVAL,
    CONF_SOLAR_PANELS,
    DEFAULT_ADDED_COSTS,
    DEFAULT_BASE_URL,
    DEFAULT_BUSINESS,
    DEFAULT_DOUBLE_METER,
    DEFAULT_GAS_ELEMENT_ID,
    DEFAULT_RETURN_COSTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOLAR_PANELS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class PureEnergieData:
    """Container for pure Energie API data."""

    def __init__(self, prices: list[dict]) -> None:
        """Initialize data container."""
        self.prices = prices


class PureEnergyCoordinator(DataUpdateCoordinator[PureEnergieData]):
    """Class to manage fetching Pure Energie price data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry,
        *,
        element_id: int | None = None,
        commodity: str | None = None,
        direction: str = "import",
    ) -> None:
        """Initialize coordinator."""
        self._entry = entry
        self._element_id = element_id
        self._commodity = commodity
        self._direction = direction

        scan_interval = entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"Pure Energie Prices ({commodity or 'default'} {direction})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.data = PureEnergieData([])

    @property
    def direction(self) -> str:
        """Return the data direction (import/export)."""
        return self._direction

    @property
    def commodity(self) -> str | None:
        """Return the commodity."""
        return self._commodity

    def _apply_cost_adjustments(
        self,
        prices: list[dict],
        now_dt: datetime | None = None,
    ) -> list[dict]:
        """Apply direction-based cost adjustments to prices.

        Only applies cost adjustments to today's prices. Next-day prices
        are left unchanged because the Pure Energie API doesn't provide
        cost breakdown data (added_costs/return_costs) for the next day
        yet - applying defaults would taint the percentile sensors.
        """
        if now_dt is None:
            now_dt = datetime.now(tz=timezone.utc)
        today_date = now_dt.date()

        for record in prices:
            # Determine the date of this price record
            record_date = self._get_record_date(record)
            if record_date is not None and record_date > today_date:
                # Skip adjustments for future days (no cost data available)
                continue

            if self._direction == "import":
                added_costs = float(
                    self._entry.data.get(CONF_ADDED_COSTS, DEFAULT_ADDED_COSTS)
                )
                if added_costs > 0:
                    record["price"] = record.get("price", 0.0) + added_costs
            elif self._direction == "export":
                return_costs = float(
                    self._entry.data.get(CONF_RETURN_COSTS, DEFAULT_RETURN_COSTS)
                )
                record["price"] = record.get("price", 0.0) + return_costs

        return prices

    def _get_record_date(self, record: dict) -> date | None:
        """Extract the date from a price record's date field."""
        # Try date.full first (nested structure: record["date"]["full"])
        date_obj = record.get("date")
        if isinstance(date_obj, dict):
            date_str = date_obj.get("full")
        else:
            date_str = None
        if not date_str:
            # Try top-level "full" field as fallback
            date_str = record.get("full")
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            return None

    def _build_current_param(self, current_dt: datetime) -> str:
        """Build the 'current' URL parameter in required format: Y-m-d H:M."""
        return current_dt.strftime("%Y-%m-%d %H:%M")

    async def _fetch_prices(
        self, current_dt: datetime
    ) -> list[dict]:
        """Fetch raw prices from the Pure Energie API."""
        entry = self._entry
        element_id = self._element_id

        commodity = self._commodity
        if commodity is None:
            # Default: use the main element_id for the entry
            commodity = (
                CONF_COMMODITY_ELECTRICITY
                if entry.data.get(CONF_COMMODITY_ELECTRICITY, True)
                else CONF_COMMODITY_GAS
            )

        # Determine element_id based on commodity
        if commodity == CONF_COMMODITY_GAS:
            element_id = entry.data.get(
                CONF_GAS_ELEMENT_ID, DEFAULT_GAS_ELEMENT_ID
            )
        else:
            element_id = element_id or entry.data.get("element_id", 11480)

        current_param = self._build_current_param(current_dt)

        business = entry.data.get(CONF_BUSINESS, DEFAULT_BUSINESS)
        double_meter = entry.data.get(CONF_DOUBLE_METER, DEFAULT_DOUBLE_METER)
        solar = entry.data.get(CONF_SOLAR_PANELS, DEFAULT_SOLAR_PANELS)

        base_url = entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL) or DEFAULT_BASE_URL

        url = (
            f"{base_url}"
            f"?double_meter={'true' if double_meter else 'false'}"
            f"&solar_panels={'true' if solar else 'false'}"
            f"&commodity={commodity}"
            f"&current={current_param}"
            f"&business={'true' if business else 'false'}"
            f"&element_id={element_id}"
        )

        session = async_get_clientsession(self.hass)
        _LOGGER.debug("Calling Pure Energie API with URL: %s", url)

        resp = await session.get(url)
        resp.raise_for_status()

        content_type = (
            resp.content_type.split(";")[0].strip().lower()
            if hasattr(resp, "content_type")
            else "unknown"
        )
        _LOGGER.debug("Pure Energie API Content-Type: %s", content_type)

        raw_json = await resp.read()

        try:
            text_content = raw_json.decode("utf-8", errors="replace")
            if not text_content.strip():
                raise UpdateFailed("Empty response")

            # Find JSON start in case of HTML wrapper
            html_start = text_content.find("{")
            if html_start >= 0:
                payload = json.loads(text_content[html_start:].strip())
            else:
                payload = json.loads(text_content.strip())

        except json.JSONDecodeError as e:
            raise UpdateFailed(f"Invalid JSON in response: {e}") from e

        prices = payload.get("prices") or []
        if not isinstance(prices, list):
            _LOGGER.warning("Expected list of price objects but got %s", type(prices))
            return []

        # Apply direction-based cost adjustments (pass now_dt for date-based skipping)
        return self._apply_cost_adjustments(prices, now_dt=current_dt)

    async def _async_update_data(self) -> PureEnergieData:
        """Fetch the latest data from the Pure Energie API."""
        try:
            now_dt = datetime.now(tz=timezone.utc)
            prices = await self._fetch_prices(now_dt)

            # Fetch next day's prices too (48h horizon is always enabled)
            next_dt = now_dt + timedelta(hours=24)
            more_prices = await self._fetch_prices(next_dt)
            prices.extend(more_prices)

            _LOGGER.debug(
                "Fetched %d prices for %s/%s",
                len(prices),
                self._commodity or "default",
                self._direction,
            )

            return PureEnergieData(prices)

        except UpdateFailed:
            raise
        except Exception as e:
            _LOGGER.warning(
                "Failed to fetch Pure Energie prices: %s. The integration will continue with stale/empty data until next successful fetch.",
                e,
            )
            return self.data
