"""Real Pure Energie API data fixture (24h)."""
from typing import Any
import json
from pathlib import Path

# Load from the fixture JSON file
_fixtures_path = Path(__file__).parent / "pure_energie_real_data.json"
_raw = json.loads(_fixtures_path.read_text())

# Type alias for the price record
class _PriceRecord:
    price: float
    unity: str
    label: str | None
    date: dict[str, Any]

class _LabelValue:
    label: str
    filters: dict[str, Any]

prices: list[dict[str, Any]] = _raw["prices"]
