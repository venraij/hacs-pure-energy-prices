# Pure Energie Prices

Custom Home Assistant integration for fetching dynamic electricity prices from Pure Energie energy company.

## Features

- Fetches real-time and forecasted electricity prices from Pure Energie API (up to 48 hours)
- Supports double meter configurations for homes with solar panels
- Calculates percentile-based pricing (e.g., 5th, 10th, 20th percentiles)
- Handles added costs and return costs for total price calculation
- Resilient API handling with graceful fallback on failures
- Configurable scan interval and horizon hours

## Installation

1. Clone this repository into your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Pure Energie Prices" and configure with your credentials

## Configuration

The integration supports the following configuration options via the Home Assistant UI:

| Option | Description | Default |
|--------|-------------|---------|
| Element ID | Pure Energie element identifier | Default value |
| Double Meter | Enable for double meter setups | True |
| Solar Panels | Enable solar panel support | True |
| Horizon Hours | Forecast horizon (24 or 48) | 24 |
| Business | Business customer flag | False |
| Commodities | Type (electricity, gas, redelivery) | electricity |
| Percentiles | Comma-separated percentile values | 0.05, 0.1, 0.2, 0.4 |
| Unit of Measurement | Price unit | €/kWh |
| Scan Interval | Update interval in seconds | 3600 |
| Added Costs | Additional costs to add | 0.0 |
| Return Costs | Costs to subtract | 0.0 |

## Usage

The integration creates the following sensor entities:

### Pure Energy Price
- **Unique ID**: `{config_entry.entry_id}_price`
- **Name**: Pure Energy Price
- **Unit**: €/kWh (configurable)
- **State Class**: MEASUREMENT
- **Description**: Displays the current electricity price

### Pure Energy Percentile Sensors
- **Unique ID**: `{config_entry.entry_id}_percentile_{value}`
- **Name**: Pure Energy {percentile}% Percentile ({percentile}%)
- **Unit**: €/kWh (configurable)
- **State Class**: MEASUREMENT
- **Description**: Displays the calculated percentile price based on forecasted data

## API Interaction

The integration fetches prices from the Pure Energie API using the following parameters:
- `double_meter`: true/false based on configuration
- `solar_panels`: true/false based on configuration
- `commodity`: electricity, gas, or redelivery
- `current`: Current timestamp
- `business`: true/false based on configuration
- `element_id`: Element identifier

## Error Handling

- Empty API responses are handled gracefully
- JSON parse failures check for HTML-wrapped responses
- API errors are logged and integration continues with stale data
- Setup continues even if initial API call fails

## Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

The test suite covers:
- Sensor creation and configuration
- Unit of measurement properties
- State class validation
- Native value calculation with data
- Native value handling with empty data
- Coordinator update methods

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
│   └── test_percentile_sensor.py
├── hacs.json                    # HACS configuration
├── pytest.ini                   # Pytest configuration
└── requirements.txt             # Dependencies
```

### Dependencies
Key dependencies include:
- aiohttp==3.13.3
- voluptuous==0.15.2
- homeassistant==2026.2.3
- astral==2.2

## License

[License information should be added]

## Support

For issues and feature requests, please use the [GitHub Issue Tracker](https://github.com/venraij/hacs-pure-energy-prices/issues).
