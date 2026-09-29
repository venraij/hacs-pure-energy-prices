# Pure Energie Prices (Custom Component)

This Home Assistant custom component fetches **Pure Energie dynamic electricity and gas prices** from the public API endpoint and exposes them as Home Assistant sensors.

It provides:
- Current price sensors for electricity and gas
- Percentile sensors to identify cheapest hours
- `prices` attribute for ApexCharts graphing
- Direction-based cost adjustments (import/export)

## Features

- Polls the Pure Energie API on a configurable interval
- Publishes:
  - Current price sensors for electricity and gas
  - Percentile sensors (5th, 10th, 20th, 40th by default)
  - `prices` attribute (raw API hourly list) on the main price sensor

## Entities

Each config entry can create:

| Sensor | When | Name |
|--------|------|------|
| Current Price | Always (if electricity enabled) | `Pure Energie Electricity - Current Price` |
| Percentile sensors | Always (if electricity enabled) | `Pure Energie Electricity - Percentile Price (5)` |
| Current Price | If solar panels enabled | `Pure Energie Electricity - Current Price` |
| Percentile sensors | If solar panels enabled | `Pure Energie Electricity - Percentile Price (5)` |
| Current Price | If gas enabled | `Pure Energie Gas - Current Price` |
| Percentile sensors | If gas enabled | `Pure Energie Gas - Percentile Price (5)` |

## Configuration

All settings are configured through the UI options flow:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| Electricity | Boolean | True | Enable electricity sensors |
| Solar panels | Boolean | False | Enable export sensors |
| Gas | Boolean | False | Enable gas sensors |
| Gas element ID | Integer | 13422 | Element identifier for gas |
| Added costs | Float | 0.0 | Additional import costs |
| Return costs | Float | 0.0 | Return costs for export |
| Scan interval | Integer (60–86400) | 3600 | Update interval in seconds |
| Double meter | Boolean | True | Use double meter reading |

## ApexCharts Integration

The main price sensor exposes `extra_state_attributes["prices"]` which you can map to ApexCharts. Each price record contains:

- `price`: float (price in kWh or m³)
- `unity`: string (unit of measurement)
- `date.full`: ISO timestamp (e.g. `2026-09-16 00:00`)
- `date.label`: human-readable label

Example: map `record.price` to the y-axis and `record.date.label` to the x-axis for a column chart.

## Installation

1. Copy the folder to `config/custom_components/pure_energy_prices/`
2. Restart Home Assistant
3. Verify sensors appear under **Entities**
