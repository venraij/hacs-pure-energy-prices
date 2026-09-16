# Pure Energie Prices - Development Guide

## Architecture

### Components

1. **Integration Entry Point** (`__init__.py`)
   - Sets up the Home Assistant integration
   - Handles config entry lifecycle
   - Creates sensor entities

2. **Data Coordinator** (`coordinator.py`)
   - `PureEnergyCoordinator`: Handles API communication
   - Fetches prices with configurable horizon (24/48 hours)
   - Implements resilience against API failures
   - Updates Home Assistant's data store

3. **Sensor Entities** (`sensor.py`)
   - `PureEnergyPriceSensor`: Displays current price
   - `PureEnergyPercentileSensor`: Displays percentile-based prices
   - Both use the coordinator for data updates

4. **Configuration Flow** (`config_flow.py`)
   - Handles UI-based setup
   - Processes user input for percentiles
   - Supports reconfiguration

### Data Flow

```
User Configuration → Config Flow → Coordinator → Pure Energie API
                                                   ↓
                                            JSON Response
                                                   ↓
                                            Coordinator Data
                                                   ↓
                                            Sensor Entities
                                                   ↓
                                            Home Assistant UI
```

## Configuration Details

### Config Flow Options

The configuration schema supports:
- **Element ID**: Pure Energie element identifier
- **Double Meter**: Boolean for double meter setups
- **Solar Panels**: Enable solar panel price handling
- **Horizon Hours**: 24 or 48 hours forecast
- **Business**: Business customer flag
- **Commodities**: electricity, gas, or redelivery
- **Percentiles**: Comma-separated list (e.g., "0.05, 0.1, 0.2, 0.4")
- **Unit of Measurement**: €/kWh or €/m³
- **Scan Interval**: Update frequency (60-86400 seconds)
- **Added Costs**: Additional costs to add to prices
- **Return Costs**: Costs to subtract from prices

### Percentile Calculation

Percentile sensors calculate prices at specific percentiles using linear interpolation:

```python
k = (len(prices) - 1) * (percentile / 100.0)
if k == int(k):
    return prices[int(k)]
else:
    i = int(k)
    f = k - i
    return round(prices[i] + f * (prices[i+1] - prices[i]), 2)
```

## API Integration

### Endpoint Construction

The integration constructs API URLs with these parameters:
- `double_meter`: Boolean for double meter configuration
- `solar_panels`: Boolean for solar panel support
- `commodity`: Commodity type (electricity, gas, redelivery)
- `current`: Current timestamp
- `business`: Business customer flag
- `element_id`: Element identifier

### Response Handling

1. Fetches JSON response from Pure Energie API
2. Handles HTML-wrapped responses
3. Validates JSON structure
4. Calculates added/return costs
5. Updates coordinator data

## Testing

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_percentile_sensor.py

# Run with verbose output
pytest -v
```

### Test Structure

- `conftest.py`: Shared fixtures
- `test_percentile_sensor.py`: Sensor functionality tests

### Test Coverage

Tests cover:
- Sensor creation and initialization
- Configuration properties
- Unit of measurement
- State class validation
- Native value calculation
- Empty data handling
- Coordinator updates

## Development Workflow

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Make Changes**
   - Edit code in `custom_components/pure_energy_prices/`
   - Update tests as needed

3. **Run Tests**
   ```bash
   pytest
   ```

4. **Debug**
   - Check Home Assistant logs
   - Use coordinator debug logging
   - Monitor API responses

## Error Handling

The integration implements several error handling strategies:

1. **API Failures**: Continue with stale data
2. **Empty Responses**: Raise UpdateFailed
3. **JSON Parse Errors**: Check for HTML-wrapped responses
4. **Missing Data**: Return None for sensor values

## Deployment

### HACS Installation

1. Add repository to HACS
2. Browse and install "Pure Energie Custom Prices"
3. Restart Home Assistant
4. Configure via UI

### Manual Installation

1. Copy `pure_energy_prices/` to `custom_components/`
2. Restart Home Assistant
3. Add integration via UI

## Maintenance

### Updating

1. Pull latest changes
2. Restart Home Assistant
3. Verify integration works

### Troubleshooting

1. Check Home Assistant logs for errors
2. Verify API connectivity
3. Confirm configuration is correct
4. Test with manual API calls
