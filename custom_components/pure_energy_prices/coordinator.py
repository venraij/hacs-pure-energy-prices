from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp
import json
import logging
import urllib.parse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    BASE_URL,
    CONF_ELEMENT_ID,
    CONF_DOUBLE_METER,
    CONF_SOLAR_PANELS,
    CONF_BUSINESS,
    CONF_SCAN_INTERVAL,
    CONF_HORIZON_HOURS,  # int: 24 or 48
    CONF_ADDED_COSTS,
    CONF_RETURN_COSTS,
    CONF_COMMODITY,
)

_LOGGER = logging.getLogger(__name__)

type PureEnergieConfigEntry = ConfigEntry[PureEnergyData]


@dataclass
class PureEnergyData:
    """Class to hold your data."""

    prices: list[dict[str, Any]]


class PureEnergyCoordinator(DataUpdateCoordinator[PureEnergyData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
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

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()

                if not resp.ok:
                    text = await resp.text()
                    raise UpdateFailed(f"HTTP error {resp.status}: {text[:500]}")

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
        horizon_hours: int = int(self.entry.data.get(CONF_HORIZON_HOURS, 24))  # 24 or 48
        now_dt = dt_util.now()

        try:
            prices: list[dict[str, Any]] = await self._fetch_prices(now_dt)

            if horizon_hours == 48:
                next_dt = now_dt + timedelta(hours=24)
                more_prices = await self._fetch_prices(next_dt)
                prices.extend(more_prices)

            added_costs: float = float(self.entry.data.get(CONF_ADDED_COSTS, 0.0))
            return_costs: float = float(self.entry.data.get(CONF_RETURN_COSTS, 0.0))
            if added_costs:
                for record in prices:
                    record["price"] = record.get("price", 0.0) + added_costs + return_costs

        except Exception as e:
            raise UpdateFailed(f"Failed to fetch Pure Energie prices: {e}") from e

        return PureEnergyData(prices)
