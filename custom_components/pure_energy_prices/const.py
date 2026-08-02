DOMAIN = "pure_energy_prices"
BASE_URL = "https://pure-energie.nl/api/prices-element/dynamic/"

CONF_ELEMENT_ID = "element_id"
CONF_DOUBLE_METER = "double_meter"
CONF_SOLAR_PANELS = "solar_panels"
CONF_BUSINESS = "business"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_HORIZON_HOURS = "horizon_hours"
CONF_ADDED_COSTS = "added_costs"

DEFAULT_ELEMENT_ID: int = 11480
DEFAULT_DOUBLE_METER: bool = True
DEFAULT_SOLAR_PANELS: bool = True
DEFAULT_BUSINESS: bool = False
DEFAULT_SCAN_INTERVAL: int = 3600
DEFAULT_HORIZON_HOURS: int = 24
DEFAULT_ADDED_COSTS: float = 0.0
