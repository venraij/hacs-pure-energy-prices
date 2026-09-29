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

## Components

### Coordinator (`coordinator.py`)

The coordinator (`PureEnergieCoordinator`) handles:

- Fetching price data from the Pure Energie API every 48 hours
- Parsing JSON responses (handles HTML-wrapped JSON)
- Applying direction-based cost adjustments (import adds costs, export subtracts)
- Managing two sensor streams per commodity: import and export

### Sensors (`sensor.py`)

| Class | Purpose | Name |
|-------|---------|------|
| `PureEnergiePriceSensor` | Current price (first record) | `Pure Energie {Commodity} - Current Price` |
| `PureEnergiePercentileSensor` | Price percentile threshold | `Pure Energie {Commodity} - Percentile Price (X)` |

Each config entry creates:
- **Electricity import** sensor (always, if electricity enabled)
- **Electricity export** sensor (if solar panels enabled)
- **Gas import** sensor (if gas enabled)
- **Percentile sensors** for each direction (5th, 10th, 20th, 40th by default)

### Configuration Flow (`config_flow.py`)

Fields in setup and options:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `electricity` | Boolean | True | Enable electricity sensors |
| `solar_panels` | Boolean | False | Enable export sensors |
| `gas` | Boolean | False | Enable gas sensors |
| `gas_element_id` | Integer | 13422 | Gas element identifier |
| `added_costs` | Float | 0.0 | Additional import costs |
| `return_costs` | Float | 0.0 | Return costs for export |
| `scan_interval` | Integer (60–86400) | 3600 | Update interval in seconds |
| `double_meter` | Boolean | True | Use double meter reading |

**Note**: `horizon_hours` is hardcoded to 48 hours and is not configurable.

### Constants (`const.py`)

| Constant | Value |
|----------|-------|
| `DOMAIN` | `pure_energy_prices` |
| `DEFAULT_BASE_URL` | `https://pure-energie.nl/api/prices-element/dynamic` |
| `DEFAULT_SCAN_INTERVAL` | 3600 |
| `DEFAULT_GAS_ELEMENT_ID` | 13422 |
| `DEFAULT_PERCENTILES` | `0.05,0.1,0.2,0.4` |
| `DEFAULT_ADDED_COSTS` | 0.0 |
| `DEFAULT_RETURN_COSTS` | 0.0 |

## API Integration

### URL Construction

```
https://pure-energie.nl/api/prices-element/dynamic/?double_meter={bool}&solar_panels={bool}&commodity={str}&current={str}&business={bool}&element_id={str}
```

Parameters:
- `double_meter` — from config, default `true`
- `solar_panels` — from config, default `false`
- `commodity` — `electricity` or `gas`
- `current` — formatted as `YYYY-MM-DD HH:MM`
- `business` — from config, default `false`
- `element_id` — from config

### Response Processing

1. Check `Content-Type` header for `application/json`
2. If present, parse directly. Otherwise, search for `{` in response body (handles HTML-wrapped JSON)
3. Empty responses raise `UpdateFailed("Empty response")`
4. Invalid JSON raises `UpdateFailed` with context

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Connection failure | Logged; returns stale data |
| Non-200 status | Caught by `_async_update_data`, logged |
| Invalid JSON | Parses from HTML wrapper if possible, otherwise raises |
| Empty body | Raises `UpdateFailed("Empty response")` |

## Data Model

### PureEnergieData

```python
class PureEnergieData:
    prices: list[dict]  # Raw API response
```

### Price Record

```python
{
    "price": float,      # Price in €/kWh or €/m³
    "unity": string,     # Unit of measurement
    "date": {
        "full": string,  # ISO timestamp (e.g. "2026-09-16 00:00")
        "label": string  # Human-readable label
    }
}
```

### Sensor Attributes

The main price sensor exposes `extra_state_attributes["prices"]` — the full list of price records. This is used by ApexCharts to render column charts.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_percentiles_constant.py -v
```

## Version History

| Version | Change |
|---------|--------|
| 2 | Current version — multi-sensor support with percentile calculations |

## HACS Integration

- `content_in_root: false` — installed as sub-directory
- `render_readme: true` — repository README shown on integration card

