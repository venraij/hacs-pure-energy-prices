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

## Configuration Options and Their Impact

This section explains the purpose and consequence of each configurable option. Misconfiguration here can lead to incorrect data being displayed.

*   **`element_id` (Required):** The unique identifier for your energy contract. This is essential for the API to fetch data for your specific service.
*   **`double_meter` (Boolean):** If set to `true`, the API call includes parameters for a double meter setup. If this is incorrect for your contract, the returned prices will be wrong.
*   **`solar_panels` (Boolean):** If `true`, the API query includes parameters for solar panel integration. If set incorrectly, the prices displayed may not account for your generation.
*   **`business` (Boolean):** Distinguishes between residential and commercial contracts. Setting this incorrectly will fetch data for the wrong customer type.
*   **`horizon_hours` (Integer):** Defines how far into the future the prices are calculated (e.g., `24` for one day, `48` for two days).
*   **`commodity` (Enum):** Selects the type of energy (`electricity`, `gas`, `redelivery`). Ensure this matches your contract exactly.
*   **`percentiles` (String):** Specifies the percentile values to track (e.g., `"10, 50, 90"`). **This is the most fragile setting; ensure only comma-separated numeric values are used.**

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