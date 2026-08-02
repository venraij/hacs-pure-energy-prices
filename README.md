# Pure Energie Prices

A Home Assistant integration that fetches dynamic electricity prices from [Pure Energie](https://pure-energie.nl/) and exposes them as sensors.

This integration is available via [HACS](https://hacs.xyz/).

## Features

- **Dynamic Pricing Sensor**: Provides the current all-in electricity price per kWh.
- **Price History Attribute**: Exposes the full hourly price list as an attribute, making it easy to visualize trends.
- **Configurable**: Supports various settings such as:
  - Double meter support
  - Solar panel configuration
  - Business vs. Residential profiles
  - Custom scan intervals
- **HACS Ready**: Easy installation and updates through the Home Assistant Community Store.

## Installation

### Via HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click on **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Paste the URL: `https://github.com/venraij/hacs-pure-energy-prices`
5. Select **Integration** as the category.
6. Click **Add**.
7. Search for **Pure Energie Prices** and click **Download**.
8. **Restart Home Assistant**.

### Manual Installation

1. Download the repository as a ZIP file.
2. Extract the contents of `custom_components/pure_energy_prices` into your Home Assistant `/config/custom_components/` directory.
3. **Restart Home Assistant**.

## Configuration

After restarting, go to **Settings** > **Devices & Services** > **Add Integration** and search for **Pure Energie Prices**.

During setup, you will be prompted to provide your `element_id` (found in your Pure Energie account) and other relevant settings like whether you have a double meter or solar panels.

## Usage

### Sensors

The integration creates a sensor with the following characteristics:

- **State**: The current all-in electricity price (e.g., `0.25`).
- **Unit of Measurement**: `€/kWh`
- **Attributes**:
  - `prices`: A list of dictionaries containing the hourly price data. Each dictionary typically includes:
    - `date`: An object containing the timestamp (e.g., `current: true` for the current hour).
    - `price`: The price for that hour.

### Visualization Example (ApexCharts)

You can use the `prices` attribute to create beautiful charts in Home Assistant using the [ApexCharts Card](https://github.com/RomRider/apexcharts-card).

```yaml
type: custom:apexcharts-card
graph_span: 48h
span:
  start: day
now:
  show: true
  label: Nu
header:
  show: true
  title: Energieprijs per uur (€/kwh)
series:
  - entity: sensor.pure_energie_price
    show:
      legend_value: false
    stroke_width: 2
    float_precision: 3
    type: column
    opacity: 0.3
    color: "#03b2cb"
    data_generator: |
      return (entity.attributes.prices || []).map((record) => {
        // record.date.full example: "2026-07-31 16:00"
        const x = Date.parse(record.date.full);
        const y = record.price;
        return [x, y];
      });
```


*(Note: Adjust the `entity` ID to match your actual sensor entity ID.)*

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT](LICENSE)

