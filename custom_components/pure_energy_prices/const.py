DOMAIN = "pure_energy_prices"
BASE_URL = "https://pure-energie.nl/api/prices-element/dynamic/"

CONF_ELEMENT_ID = "element_id"
CONF_DOUBLE_METER = "double_meter"
CONF_SOLAR_PANELS = "solar_panels"
CONF_BUSINESS = "business"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_HORIZON_HOURS = "horizon_hours"
CONF_ADDED_COSTS = "added_costs"
CONF_RETURN_COSTS = "return_costs"
CONF_COMMODITY = "commodity"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"

DEFAULT_ELEMENT_ID: int = 11480
DEFAULT_DOUBLE_METER: bool = True
DEFAULT_SOLAR_PANELS: bool = True
DEFAULT_BUSINESS: bool = False
DEFAULT_SCAN_INTERVAL: int = 3600
DEFAULT_HORIZON_HOURS: int = 24
DEFAULT_ADDED_COSTS: float = 0.0
DEFAULT_RETURN_COSTS: float = 0.0
DEFAULT_COMMODITY: str = "electricity"
DEFAULT_UNIT_OF_MEASUREMENT: str = "€/kWh"