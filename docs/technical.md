# Pure Energie Prices — Technical Documentation

## Architecture

The integration follows the Home Assistant custom component pattern with a coordinator-based data fetch model.

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  HA UI /    │────>│  ConfigFlow  │────>│  Coordinator     │────>│ Pure Energie    │
│  Config     │     │              │     │                  │     │ REST API        │
└─────────────┘     └──────────────┘     └────────┬─────────┘     └─────────────────┘
                                                  │
                                          ┌───────▼─────────┐
                                          │  Sensor Entities │
                                          │  (Price +        │
                                          │   Percentile)    │
                                          └─────────────────┘
```

## Component Overview

| File | Role |
|------|------|
| `__init__.py` | Entry point — sets up/unloads the integration, creates entities |
| `coordinator.py` | Data fetcher — talks to Pure Energie API, populates shared data |
| `sensor.py` | Entities — `PureEnergyPriceSensor` + `PureEnergyPercentileSensor` |
| `config_flow.py` | Setup wizard — UI form, validation, reconfigure support |
| `const.py` | Constants — domain, config keys, defaults |
| `manifest.json` | Metadata — version, dependencies, codeowners |

## Data Flow

1. User configures the integration via HA UI (`config_flow.py`).
2. On startup, `async_setup_entry` creates a `PureEnergyCoordinator` and calls `async_config_entry_first_refresh()`.
3. The coordinator builds the API URL using config options, fetches JSON from Pure Energie, and stores it in `self.data`.
4. On each scan interval, `async_update_data` re-fetches, parses, applies cost adjustments, and triggers entity updates.
5. Sensor entities read from the coordinator's `data` dict on each property access.

```
ConfigEntry ──> Coordinator.__init__ ──> scan_interval set
                        │
                        ▼
            async_config_entry_first_refresh()
                        │
                        ▼
            coordinator._async_update_data()
                        │
                  ┌─────▼──────┐
                  │ _fetch_    │
                  │ prices()   │
                  └─────┬──────┘
                        │
                  ┌─────▼──────┐
                  │ _fetch_    │
                  │ additional │
                  └─────┬──────┘
                        │
                  ┌─────▼──────┐
                  │ JSON parse │
                  │ + cost adj │
                  └─────┬──────┘
                        │
                        ▼
                  coordinator.data = PureEnergyData(prices)
                        │
                        ▼
                  sensors refresh via property getters
```

## Coordinator Details

### PureEnergyCoordinator

**Module**: `coordinator.py`

Inherits from `DataUpdateCoordinator[PureEnergyData]`.

#### Configuration

| Option | Source | Purpose |
|--------|--------|---------|
| `CONF_HORIZON_HOURS` | `entry.data` | Forecast window: 24 or 48 hours |
| `CONF_SCAN_INTERVAL` | `entry.data` | Seconds between API calls |

#### Methods

**`_async_update_data()`**

Fetches prices, applies adjustments, returns `PureEnergyData`.

```python
async def _async_update_data(self) -> PureEnergyData:
    horizon = int(self.entry.data.get(CONF_HORIZON_HOURS, 24))
    now = dt_util.now()
    prices = await self._fetch_prices(now)
    
    if horizon == 48:
        next_dt = now + timedelta(hours=24)
        more = await self._fetch_additional_prices(next_dt)
        prices.extend(more)
    
    added = float(self.entry.data.get(CONF_ADDED_COSTS, 0.0))
    returned = float(self.entry.data.get(CONF_RETURN_COSTS, 0.0))
    
    for record in prices:
        record["price"] += added
        record["price"] -= returned
    
    return PureEnergyData(prices)
```

**`_fetch_prices(datetime)`**

Builds the URL, sends the GET request, parses the JSON response.

```python
async def _fetch_prices(self, dt: datetime) -> list[dict]:
    session = async_get_clientsession(self.hass)
    
    url = f"{BASE_URL}?double_meter={...}&solar_panels={...}" \
          f"&commodity={...}&current={...}&business={...}" \
          f"&element_id={...}"
    
    resp = await session.get(url)
    resp.raise_for_status()
    
    text = await resp.read()
    data = json.loads(text.decode("utf-8"))
    
    return data["prices"]
```

**Resilience strategy**: if the API call or JSON parse fails, the error is logged but the current data (even if stale/empty) is returned so that setup doesn't block and entities can still report.

## Sensor Entities

### PureEnergyPriceSensor

**Module**: `sensor.py`

| Property | Value |
|----------|-------|
| `unique_id` | `{config_entry.entry_id}_price` |
| `name` | `"Pure Energy Price"` |
| `native_value` | First price from `coordinator.data.prices`, rounded to 2 dp |
| `unit_of_measurement` | From config, default `€/kWh` |
| `state_class` | `SensorStateClass.MEASUREMENT` |

**Value calculation**:

```python
@property
def native_value(self) -> float | None:
    data = self.coordinator.data if hasattr(self.coordinator, "data") else {}
    if isinstance(data, list) and data:
        return round(data[0].get("price", 0.0), 2)
    return None
```

### PureEnergyPercentileSensor

**Module**: `sensor.py`

| Property | Value |
|----------|-------|
| `unique_id` | `{config_entry.entry_id}_percentile_{N}` |
| `name` | `"Pure Energy {N}% Percentile ({N}%)"` |
| `native_value` | Interpolated price at given percentile |
| `unit_of_measurement` | From config, default `€/kWh` |
| `state_class` | `SensorStateClass.MEASUREMENT` |

**Percentile calculation** (linear interpolation):

```
k    = (len(prices) - 1) * (percentile / 100)
i    = int(k)
f    = k - i          # fractional part

if k == i:
    return prices[i]
else:
    return round(prices[i] + f * (prices[i+1] - prices[i]), 2)
```

Falls back to `None` on any error (index out of range, missing data, type mismatch).

## Configuration Schema

**Module**: `config_flow.py`

```python
vol.Schema({
    vol.Required(CONF_ELEMENT_ID, default=DEFAULT_ELEMENT_ID): positive_int,
    vol.Required(CONF_DOUBLE_METER, default=DEFAULT_DOUBLE_METER): bool,
    vol.Required(CONF_SOLAR_PANELS, default=DEFAULT_SOLAR_PANELS): bool,
    vol.Required(CONF_HORIZON_HOURS, default=DEFAULT_HORIZON_HOURS): positive_int,
    vol.Required(CONF_BUSINESS, default=DEFAULT_BUSINESS): bool,
    vol.Optional(CONF_COMMODITY, default=DEFAULT_COMMODITY): vol.In(["electricity", "gas", "redelivery"]),
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): vol.In(["€/kWh", "€/m³"]),
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(positive_int, vol.Range(min=60, max=86400)),
    vol.Optional(CONF_PERCENTILES, default=DEFAULT_PERCENTILES): str,       # stored as list internally
    vol.Optional(CONF_ADDED_COSTS, default=DEFAULT_ADDED_COSTS): small_float,
    vol.Optional(CONF_RETURN_COSTS, default=DEFAULT_RETURN_COSTS): small_float,
})
```

Percentiles are stored as a Python `list[float]` in config entry data but displayed as a comma-separated string in the UI. Invalid input is caught and reported in Dutch: *"De waarden voor PERCENTILES moeten geldige numerieke waarden zijn…"*

## Constants Reference

**Module**: `const.py`

### Domain
| Key | Value |
|-----|-------|
| `DOMAIN` | `"pure_energy_prices"` |

### Configuration Keys
| Key | Default | Type |
|-----|---------|------|
| `CONF_ELEMENT_ID` | `"default"` | int |
| `CONF_DOUBLE_METER` | `True` | bool |
| `CONF_SOLAR_PANELS` | `True` | bool |
| `CONF_HORIZON_HOURS` | `24` | int |
| `CONF_BUSINESS` | `False` | bool |
| `CONF_COMMODITY` | `"electricity"` | str |
| `CONF_UNIT_OF_MEASUREMENT` | `"€/kWh"` | str |
| `CONF_SCAN_INTERVAL` | `60` | int (min 60, max 86400) |
| `CONF_PERCENTILES` | `0.05, 0.1, 0.2, 0.4` | str→list[float] |
| `CONF_ADDED_COSTS` | `0.0` | float |
| `CONF_RETURN_COSTS` | `0.0` | float |

## API Integration

### URL Construction

The coordinator builds the API URL from these parameters:

```
{BASE_URL}?double_meter={bool}&solar_panels={bool}&commodity={str}&current={str}&business={bool}&element_id={str}
```

- `double_meter` — from `CONF_DOUBLE_METER`, default `true`
- `solar_panels` — from `CONF_SOLAR_PANELS`, default `true`
- `commodity` — from `CONF_COMMODITY`: `electricity`, `gas`, or `redelivery`
- `current` — timestamp formatted as `YYYY-MM-DD HH:MM`
- `business` — from `CONF_BUSINESS`, default `false`
- `element_id` — from `CONF_ELEMENT_ID`

### Response Processing

1. Check `Content-Type` header — if starts with `application/json`, parse directly.
2. If not, search for `{` in the response body and parse from that position (handles HTML-wrapped JSON).
3. Empty responses raise `UpdateFailed("Empty response")`.
4. Any parse error is logged with the raw bytes and raised.

### Error Handling Summary

| Scenario | Behavior |
|----------|----------|
| API timeout / connection error | Logged, coordinator returns stale data |
| Non-200 status | `resp.raise_for_status()` raises, caught by `_async_update_data` |
| Invalid JSON | Checks for HTML wrapper; if still invalid, raises `UpdateFailed` |
| Empty body | Raises `UpdateFailed("Empty response")` |
| Missing fields in price dict | Graceful `get()` with defaults |

## Testing

### Structure

```
tests/
├── conftest.py                     # Pytest fixtures (mock entry, coordinator)
└── test_percentile_sensor.py       # PureEnergyPercentileSensor tests
```

### Running

```bash
pytest                               # all tests
pytest tests/test_percentile_sensor.py   # single file
pytest -v                            # verbose
pytest -m "not slow"                 # skip slow markers
```

### Test Matrix

| Test | What it verifies |
|------|-----------------|
| `test_sensor_creation` | Constructor accepts coordinator, config, percentile |
| `test_unit_of_measurement` | Returns config value or defaults to `€/kWh` |
| `test_state_class` | Returns `SensorStateClass.MEASUREMENT` |
| `test_native_value_with_data` | Interpolation works with sample prices |
| `test_native_value_empty_data` | Returns `None` when no prices |
| `test_update` | Coordinator `async_update_data` is called on update |

## HACS Integration

**File**: `hacs.json`

```json
{
  "name": "Pure Energie Custom Prices",
  "content_in_root": false,
  "render_readme": true
}
```

Installed as a sub-directory under `custom_components/` (`content_in_root: false`). HACS will render the repository README on the integration card (`render_readme: true`).
