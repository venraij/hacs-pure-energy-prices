# Pure Energie Custom Prices (Custom Component)

This Home Assistant custom component fetches **Pure Energie dynamic electricity prices** from the public API endpoint and exposes them as Home Assistant sensors.

It provides:
- A sensor that exposes the full hourly `prices` list as an attribute
- A sensor that exposes the current hour’s all-in price (based on `date.current`)

## Features
- Polls the Pure Energie API every hour
- Publishes:
  - `prices` attribute (raw API hourly list)
  - `current all-in price` sensor

## Installation
1. Copy the folder to:
   - `/config/custom_components/pure_energy_custom/`
2. Restart Home Assistant.
3. Verify sensors appear under **Entities**.

## ApexCharts example
The `prices` sensor contains an attribute `prices` which you can map to ApexCharts.
(Adjust the `entity:` to the actual entity_id created by Home Assistant.)

Example data generator (conceptual):
- x-axis from `record.date.full`
- y-axis from `record.price`

## Notes
- The component is a template/example implementation; you may need to adjust the endpoint parameters or `element_id` for your contract.
