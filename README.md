# Pure Energie Prices

Home Assistant integration for Pure Energie dynamic electricity and gas prices.

## Features

- **Multi-commodity support**: Electricity and gas
- **Per-entry multi-sensor**: Each config entry can create multiple sensor entities (import/export)
- **Percentile sensors**: Pre-calculated percentile prices from forecasted data
- **Price direction awareness**: Import adds costs, export subtracts return costs
- **Reconfiguration support**: Update options without reinstalling

## Configuration

### Setup

Add the integration through the Home Assistant UI. On first setup you configure:

- **Electricity**: Enable electricity sensors (default: on)
- **Solar panels**: Enable solar panel/export sensors (default: off)
- **Gas**: Enable gas sensors (default: off)
- **Gas element ID**: Element identifier for gas prices
- **Added costs**: Additional costs added to import prices
- **Return costs**: Costs subtracted from export prices
- **Scan interval**: Update interval in seconds (60–86400)
- **Double meter**: Use double meter reading (default: on)

### Options

After setup, access options via the integration options flow to update:
- Commodity toggles
- Cost adjustments
- Scan interval
- Double meter setting

**Note**: `horizon_hours` is now fixed at 48 hours and is no longer configurable.

### Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `electricity` | bool | True | Enable electricity sensors |
| `solar_panels` | bool | False | Enable solar panel/export sensors |
| `gas` | bool | False | Enable gas sensors |
| `gas_element_id` | int | 13422 | Element identifier for gas prices |
| `added_costs` | float | 0.0 | Costs added to import prices |
| `return_costs` | float | 0.0 | Costs subtracted from export prices |
| `scan_interval` | int | 3600 | Update interval in seconds (60–86400) |
| `double_meter` | bool | True | Use double meter reading |

**Note**: `horizon_hours` is hardcoded to 48 hours and no longer configurable.

## Entities

### Electricity Sensors

Each config entry creates:

- **Electricity Import**: Import price for the current hour + percentile sensors
- **Electricity Export**: Export price sensor + percentile sensors (when solar panels enabled)
- **Percentile Sensors**: Multiple percentile price sensors per direction (5th, 10th, 20th, 40th by default)

### Gas Sensors

- **Gas Import**: Current gas price sensor + percentile sensors

### Updates

- Prices are fetched from the API every **scan interval** (default: every hour).
- The price sensors show the price of the **current hour** in Home Assistant's
  local time zone, matched on `date.full`, and update at the start of every
  hour, even between fetches.
- If the current hour is not in the fetched data, the sensor falls back to the
  entry the API marked as `current`, and then to the first entry.

### Sensor Naming

| Sensor | Name Format |
|--------|-------------|
| Current Price | `Pure Energie {Commodity} - Current Price` |
| Percentile | `Pure Energie {Commodity} - Percentile Price (X)` |
| e.g. 5th percentile | `Pure Energie Electricity - Percentile Price (5)` |
| e.g. 10th percentile | `Pure Energie Electricity - Percentile Price (10)` |
| e.g. 20th percentile | `Pure Energie Electricity - Percentile Price (20)` |
| e.g. 40th percentile | `Pure Energie Electricity - Percentile Price (40)` |

### Using Percentile Sensors for Cheapest Hours

The percentile sensors show price thresholds. If the **Current Price** sensor value is below a percentile threshold, that hour is among the cheapest X% of the day:

- **5th percentile**: Price below which 5% of hourly prices fall
- **10th percentile**: Price below which 10% of hourly prices fall
- **20th percentile**: Price below which 20% of hourly prices fall
- **40th percentile**: Price below which 40% of hourly prices fall

### Using the Prices Attribute with ApexCharts

The main price sensor exposes `extra_state_attributes["prices"]` — a list of hourly price records. Each record contains:

- `price`: float (€/kWh or €/m³)
- `unity`: string (unit)
- `date.full`: ISO timestamp (e.g. `2026-09-16 00:00`)
- `date.label`: human-readable label

This can be mapped to ApexCharts for a column chart of hourly prices.

## API Interaction

The integration fetches prices from the Pure Energie API using:

- `double_meter`: true/false
- `solar_panels`: true/false
- `commodity`: electricity or gas
- `current`: Current local timestamp (Home Assistant time zone)
- `business`: true/false
- `element_id`: Element identifier

URL format:
```
https://pure-energie.nl/api/prices-element/dynamic/?double_meter=true&solar_panels=true&commodity=electricity&current=2026-09-29+10:25&business=false&element_id=11480
```

## Error Handling

- Empty API responses handled gracefully
- JSON parse failures check for HTML-wrapped responses
- API errors logged; integration continues with stale data
- Setup continues even if initial API call fails

## Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_percentiles_constant.py -v
```

Test coverage includes:
- Sensor creation and configuration
- Unit of measurement properties
- State class validation
- Percentile constant usage
- Price adjustment by direction (import adds costs, export subtracts)
- Configuration defaults
- Version pin correctness

## Development

### Project Structure

```
pure-energie-prices/
├── custom_components/
│   └── pure_energy_prices/
│       ├── __init__.py          # Integration setup
│       ├── sensor.py            # Sensor entities
│       ├── coordinator.py       # Data fetcher
│       ├── config_flow.py       # Configuration flow
│       ├── const.py             # Constants
│       ├── manifest.json        # Integration metadata
│       └── brand/               # Brand assets
├── docs                         # Documentation
├── tests/
│   ├── conftest.py              # Test fixtures
│   └── test_*.py                # Test files
├── hacs.json                    # HACS configuration
├── pytest.ini                   # Pytest configuration
└── requirements.txt             # Dependencies
```

### Dependencies

- aiohttp
- voluptuous
- homeassistant
- astral

## License

[License information should be added]

## Support

For issues and feature requests, please use the [GitHub Issue Tracker](https://github.com/venraij/hacs-pure-energy-prices/issues)
