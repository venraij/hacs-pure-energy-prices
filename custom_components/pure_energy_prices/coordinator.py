from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import json
import logging
import urllib.parse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    BASE_URL,
    CONF_ADDED_COSTS,
    CONF_BUSINESS,
    CONF_COMMODITY,
    CONF_DOUBLE_METER,
    CONF_ELEMENT_ID,
    CONF_HORIZON_HOURS,
    CONF_RETURN_COSTS,
    CONF_SCAN_INTERVAL,
    CONF_SOLAR_PANELS,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

@dataclass
class PureEnergyData:
    """Class to hold your data."""
    prices: list[dict[str, Any]]

PureEnergieConfigEntry = ConfigEntry[PureEnergyData]

class PureEnergyCoordinator(DataUpdateCoordinator[PureEnergyData]):
    def __init__(self, hass: HomeAssistant, entry: PureEnergieConfigEntry) -> None:
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name="Pure Energie Prices",
            update_interval=timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL, 3600)),
        )
        self.data = PureEnergyData([])

    def _build_current_param(self, current_dt) -> str:
        # Required format: Y-m-d H:i
        current_str = current_dt.strftime("%Y-%m-%d %H:%M")
        return urllib.parse.quote_plus(current_str)

    async def _fetch_prices(self, current_dt) -> list[dict[str, Any]]:
        p = self.entry.data
        current_param = self._build_current_param(current_dt)

        url = (
            f"{BASE_URL}"
            f"?double_meter={'true' if p.get(CONF_DOUBLE_METER, True) else 'false'}"
            f"&solar_panels={'true' if p.get(CONF_SOLAR_PANELS, True) else 'false'}"
            f"&commodity={p.get(CONF_COMMODITY)}"
            f"&current={current_param}"
            f"&business={'true' if p.get(CONF_BUSINESS, False) else 'false'}"
            f"&element_id={p.get(CONF_ELEMENT_ID)}"
        )

        session = async_get_clientsession(self.hass)
        _LOGGER.info("Calling with call: %s", url)

        async with await session.get(url) as resp:
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

                payload = json.loads(text_content.strip())

            except Exception as e:
                _LOGGER.warning(
                    "JSON parse failed, checking if wrapped in HTML... (error=%s)", e
                )

                text_content = raw_json.decode("utf-8", errors="replace")
                html_start = text_content.find("{")
                if html_start >= 0:
                    payload = json.loads(text_content[html_start:].strip())
                else:
                    raise UpdateFailed(
                        f"Response appears to be {content_type} HTML wrapper "
                        f"(first bytes show no valid JSON): {text_content[:100]}"
                    ) from e

        prices = payload.get("prices") or []
        if not isinstance(prices, list):
            _LOGGER.warning("Expected list of price objects but got %s", type(prices))
            return []

        return prices

    async def _async_update_data(self) -> PureEnergyData:
        """Fetches prices and updates the coordinator's data. Implements resilience against API failures."""
        try:
            horizon_hours: int = int(self.entry.data.get(CONF_HORIZON_HOURS, 24))  # 24 or 48
            now_dt = dt_util.now()

            prices: list[dict[str, Any]] = await self._fetch_prices(now_dt)

            if horizon_hours == 48:
                next_dt = now_dt + timedelta(hours=24)
                more_prices = await self._fetch_prices(next_dt)
                prices.extend(more_prices)

            added_costs: float = float(self.entry.data.get(CONF_ADDED_COSTS, 0.0))
            return_costs: float = float(self.entry.data.get(CONF_RETURN_COSTS, 0.0))
            
            # Apply added/return costs to all price records
            for record in prices:
                record["price"] = record.get("price", 0.0) + added_costs + return_costs
            
            return PureEnergyData(prices)

        except UpdateFailed as e:
            # Catch API failures and prevent them from causing a fatal ConfigEntryNotReady during setup
            _LOGGER.warning("Failed to fetch Pure Energie prices: %s. The integration will continue with stale/empty data until next successful fetch.", e)
            # Return the current data (which might be empty) to allow setup to complete
            return self.data
        except Exception as e:
            _LOGGER.error("An unexpected error occurred during price fetching: %s", e)
            # Also return current data on unexpected failure
            return self.data