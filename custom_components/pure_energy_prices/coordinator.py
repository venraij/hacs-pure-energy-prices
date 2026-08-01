
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    BASE_URL,
    CONF_ELEMENT_ID,
    CONF_DOUBLE_METER,
    CONF_SOLAR_PANELS,
    CONF_BUSINESS,
    CONF_SCAN_INTERVAL,
    CONF_COMMODITY
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

    async def _async_update_data(self) -> PureEnergyData:
        p = self.entry.data
        url = (
            f"{BASE_URL}"
            f"?double_meter={'true' if p.get(CONF_DOUBLE_METER, True) else 'false'}"
            f"&solar_panels={'true' if p.get(CONF_SOLAR_PANELS, True) else 'false'}"
            f"&commodity={'gas' if p.get(CONF_COMMODITY, "gas") else 'electricity'}"
            f"&current=null"
            f"&business={'true' if p.get(CONF_BUSINESS, False) else 'false'}"
            f"&element_id={p.get(CONF_ELEMENT_ID)}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()

                    # Check status first (200 is OK!)
                    if not resp.ok:
                        text = await resp.text()
                        raise UpdateFailed(f"HTTP error {resp.status}: {text[:500]}")
               
                    content_type = resp.content_type.split(';')[0].strip().lower() if hasattr(resp, 'content_type') else "unknown"
                    
                    _LOGGER.debug("Pure Energie API Content-Type: %s", content_type)

                    # Read raw JSON data first - don't depend on aiohttp's automatic conversion logic which 
                    # can fail with wrong Content-Types (text/html instead of application/json)
                    try:
                        raw_json = await resp.read()  # This reads the response body without converting
                        
                    except Exception as e:
                        raise UpdateFailed(f"Cannot read response: {e}") from e
                    
                    _LOGGER.debug("Raw JSON bytes received, parsing...")

                    import json
                    payload = None
                    
                    try:
                        # Use Python's native JSON parser which is more lenient and doesn't depend on headers
                        text_content = raw_json.decode('utf-8', errors='replace')
                        
                        if not text_content.strip():
                            raise UpdateFailed("Empty response")

                        json_str = text_content.strip()
                        
                        # Try parsing - Python's json module is very lenient
                        payload = json.loads(json_str)
                        
                    except Exception as e:
                        _LOGGER.warning(f"JSON parse failed, checking if wrapped in HTML... (error={e})")
                        
                        # Sometimes APIs wrap JSON in an <html> tag or similar - try to extract the real JSON
                        import re
                        
                        html_start = text_content.find('{')  # Find start of JSON object
                        if html_start >= 0:
                            json_str = text_content[html_start:]
                            
                        else:
                            raise UpdateFailed(
                                f"Response appears to be {content_type} HTML wrapper " + 
                                f"(first bytes show no valid JSON): {text_content[:100]}"
                            )

                    _LOGGER.debug("Got %d prices from Pure Energie API", len(payload.get('prices', [])))

        except Exception as e:
            raise UpdateFailed(f"Failed to fetch Pure Energie prices: {e}") from e

        prices = payload.get("prices") or []

        if not isinstance(prices, list):
            _LOGGER.warning("Expected list of price objects but got %s", type(prices))

        return PureEnergyData(prices)