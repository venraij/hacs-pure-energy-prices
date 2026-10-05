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
    CONF_COMMODITY_REDELIVERY,
    CONF_DOUBLE_METER,
    CONF_ELEMENT_ID,
    CONF_GAS_ELEMENT_ID,
    CONF_REDELIVERY_ELEMENT_ID,
    CONF_RETURN_COSTS,
    CONF_SCAN_INTERVAL,
    CONF_SOLAR_PANELS,
    DEFAULT_ADDED_COSTS,
    DEFAULT_BASE_URL,
    DEFAULT_BUSINESS,
    DEFAULT_DOUBLE_METER,
    DEFAULT_GAS_ELEMENT_ID,
    DEFAULT_REDELIVERY_ELEMENT_ID,
    DEFAULT_RETURN_COSTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOLAR_PANELS
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

        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
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

    def _apply_cost_adjustments(self, prices: list[dict], now_dt: datetime | None = None) -> list[dict]:
        """Apply direction-based cost adjustments to prices.
        
        Args:
            prices: List of price records from API
            now_dt: Current datetime for date comparison (defaults to now UTC)
            
        Returns:
            List of price records with cost adjustments applied.
            Skips zero-priced future records.
        """
        if now_dt is None:
            now_dt = datetime.now(tz=timezone.utc)
        today_date = now_dt.date()

        added_costs = float(self._entry.data.get(CONF_ADDED_COSTS, DEFAULT_ADDED_COSTS))
        return_costs = float(self._entry.data.get(CONF_RETURN_COSTS, DEFAULT_RETURN_COSTS))

        adjusted = []
        for record in prices:
            record_date = self._get_record_date(record)
            price = record.get("price", 0.0)
            
            # Skip zero-priced records for future dates
            if record_date is not None and record_date > today_date and price == 0:
                continue
            
            # Create new record with adjustments applied
            new_record = dict(record)
            if self._direction == "import" and self._commodity == CONF_COMMODITY_ELECTRICITY and added_costs > 0:
                new_record["price"] = price + added_costs
            elif self._direction == "export":
                new_record["price"] = price - return_costs
            
            adjusted.append(new_record)
        
        return adjusted

    def _get_record_date(self, record: dict) -> date | None:
        """Extract the date from a price record's date field."""
        date_obj = record.get("date")
        if isinstance(date_obj, dict):
            date_str = date_obj.get("full")
        else:
            date_str = None
        if not date_str:
            date_str = record.get("full")
        if not date_str:
            return None
        try:
            if isinstance(date_str, str) and " " in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            else:
                dt = datetime.fromisoformat(date_str)
            return dt.date()
        except (ValueError, TypeError):
            return None

    def _build_current_param(self, current_dt: datetime) -> str:
        """Build the 'current' URL parameter."""
        return current_dt.strftime("%Y-%m-%d %H:%M")

    async def _fetch_prices(self, current_dt: datetime) -> list[dict]:
        """Fetch raw prices from the Pure Energie API."""
        entry = self._entry
        element_id = self._element_id

        commodity = self._commodity
        if commodity is None:
            commodity = CONF_COMMODITY_ELECTRICITY if entry.data.get(CONF_COMMODITY_ELECTRICITY, True) else CONF_COMMODITY_GAS

        if commodity == CONF_COMMODITY_GAS:
            element_id = entry.data.get(CONF_GAS_ELEMENT_ID, DEFAULT_GAS_ELEMENT_ID)
        elif commodity == CONF_COMMODITY_REDELIVERY:
            element_id = entry.data.get(CONF_REDELIVERY_ELEMENT_ID, DEFAULT_REDELIVERY_ELEMENT_ID)
        else:
            element_id = element_id or entry.data.get(CONF_ELEMENT_ID, DEFAULT_ELEMENT_ID)

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
        try:
            resp = await session.get(url, timeout=30)
            resp.raise_for_status()
        except aiohttp.ClientError as e:
            raise UpdateFailed(f"API request failed: {e}") from e

        content_type = resp.content_type.split(";")[0].strip().lower() if hasattr(resp, "content_type") else "unknown"
        _LOGGER.debug("Pure Energie API Content-Type: %s", content_type)

        raw_json = await resp.read()
        if not raw_json:
            raise UpdateFailed("Empty response from API")
        
        try:
            text_content = raw_json.decode("utf-8", errors="replace")
            if not text_content.strip():
                raise UpdateFailed("Empty response body")
            
            # Try to parse as pure JSON first
            payload = json.loads(text_content.strip())
        except json.JSONDecodeError:
            # If that fails, look for JSON embedded in HTML (common with some APIs)
            html_start = text_content.find("{")
            if html_start >= 0:
                try:
                    payload = json.loads(text_content[html_start:].strip())
                except json.JSONDecodeError as e:
                    raise UpdateFailed(f"Invalid JSON in HTML-wrapped response: {e}") from e
            else:
                raise UpdateFailed("No JSON found in response")

        prices = payload.get("prices") or []
        if not isinstance(prices, list):
            _LOGGER.warning("Expected list of price objects but got %s", type(prices))
            return []

        # Filter out -0 records
        filtered_prices = [p for p in prices if p.get("price", 0) != 0]
        return self._apply_cost_adjustments(filtered_prices, now_dt=current_dt)

    async def _async_update_data(self) -> PureEnergieData:
        """Fetch the latest data from the Pure Energie API."""
        try:
            now_dt = datetime.now(tz=timezone.utc)
            prices = await self._fetch_prices(now_dt)
            next_dt = now_dt + timedelta(hours=24)
            more_prices = await self._fetch_prices(next_dt)
            prices.extend(more_prices)

            _LOGGER.debug("Fetched %d prices for %s/%s", len(prices), self._commodity or "default", self._direction)
            return PureEnergieData(prices)
        except UpdateFailed:
            raise
        except Exception as e:
            _LOGGER.warning("Failed to fetch Pure Energie prices: %s. The integration will continue with stale/empty data until next successful fetch.", e)
            return self.data
