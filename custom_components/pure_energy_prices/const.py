"""Constants for the Pure Energie Prices integration."""

DOMAIN = "pure_energy_prices"

# --- Configuration keys (config flow) ---
CONF_BASE_URL = "base_url"
CONF_ELEMENT_ID = "element_id"
CONF_ADDED_COSTS = "added_costs"
CONF_BUSINESS = "business"
CONF_COMMODITY_ELECTRICITY = "electricity"
CONF_COMMODITY_GAS = "gas"
CONF_COMMODITY_REDELIVERY = "redelivery"
CONF_DOUBLE_METER = "double_meter"
CONF_GAS_ELEMENT_ID = "gas_element_id"
CONF_HORIZON_HOURS = "horizon_hours"
CONF_RETURN_COSTS = "return_costs"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SOLAR_PANELS = "solar_panels"

# --- Default values ---
DEFAULT_BASE_URL = "https://api.pure-energie.com/energy-prices"
DEFAULT_ELEMENT_ID = 11480
DEFAULT_GAS_ELEMENT_ID = 11481
DEFAULT_HORIZON_HOURS = 48
DEFAULT_ADDED_COSTS = 0.0
DEFAULT_RETURN_COSTS = 0.0
DEFAULT_SCAN_INTERVAL = 3600  # seconds
DEFAULT_BUSINESS = False
DEFAULT_DOUBLE_METER = True
DEFAULT_SOLAR_PANELS = False
DEFAULT_PERCENTILES = "0.05,0.1,0.2,0.4"
DEFAULT_COMMODITIES = ["electricity"]

# --- Units of measurement ---
UNIT_KWH = "kWh"
UNIT_M3 = "m³"
UNIT_EUR_KWH = "€/kWh"
UNIT_EUR_M3 = "€/m³"

# Sensor type / direction constants
SENSOR_TYPE_IMPORT = "import"
SENSOR_TYPE_EXPORT = "export"

# Commodity constants
COMMODITY_ELECTRICITY = "electricity"
COMMODITY_GAS = "gas"
