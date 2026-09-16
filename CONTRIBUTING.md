# Contributing to Pure Energie Prices

Thank you for your interest in contributing! This document covers the project setup and how to test your changes.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

Run tests from the project root:

```bash
# All tests
pytest

# Single file
pytest tests/test_percentile_sensor.py

# Verbose output
pytest -v
```

## Debugging the Percentile Sensor Issue

### Problem

When multiple percentiles are configured (e.g., `0.05, 0.1, 0.2, 0.4`), only the first percentile sensor entity is actually created in Home Assistant.

### Investigation Plan

**Step 1 — Check how percentiles are stored in the config entry**

Add debug logging in `sensor.py` `async_setup_entry` to print what `config_entry.data.get('percentiles')` actually returns.

- Is it a string (`"0.05, 0.1"`) or already a list (`[0.05, 0.1]`)?
- If it's a string with multiple values, does the parsing logic (lines 146-155) actually split and iterate correctly?

**Step 2 — Verify the sensor factory loop**

In `sensor.py`, lines 157-160:
```python
for percentile in percentiles:
    sensors.append(
        PureEnergyPercentileSensor(coordinator, config_entry, percentile, device_info)
    )
```
Add logging to confirm this loop is iterating over all percentiles. Check that `len(sensors)` after the loop matches the number of configured percentiles + 1 (main sensor).

**Step 3 — Check for duplicate coordinators**

`__init__.py` creates a `PureEnergyCoordinator` in `async_setup_entry` and stores it in `hass.data[DOMAIN]`. Meanwhile, `sensor.py` also creates its own `PureEnergyCoordinator(hass=hass, entry=config_entry)` on line 126.

This means **two separate coordinators** exist:
- The one in `__init__.py` that gets stored in `hass.data`
- The one in `sensor.py` that creates sensors

The `sensor.py` coordinator is **never stored in `hass.data`**, so on reload it won't share data with the `__init__.py` coordinator. Verify whether this causes issues during config reloads.

**Step 4 — Check platform registration**

In `__init__.py` line 56:
```python
return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
```

But there's no explicit `async_setup_entry` call to register the `sensor` platform — that's handled by Home Assistant's auto-discovery. Confirm that HA's platform loader correctly picks up `sensor.py`'s `async_setup_entry`.

**Step 5 — Verify async_add_entities is called**

Check that `async_add_entities(sensors)` on line 162 is actually called and that all sensors in the list get registered. Add a log entry right before that call showing `len(sensors)`.

### Quick Debug Script

Add this temporarily in `sensor.py` `async_setup_entry` right after line 146:

```python
_LOGGER.debug("Percentiles from config: %s (type: %s)", percentiles_str, type(percentiles_str))
_LOGGER.debug("Parsed percentiles: %s", percentiles)
_LOGGER.debug("Total sensors to create: %d", len(sensors))
```

Then check Home Assistant logs after setup/reload.

### Likely Fixes

1. **If the parsing is wrong** — Fix the string/list parsing to handle both formats correctly
2. **If duplicate coordinators** — Remove the coordinator from `sensor.py` and get the shared one from `hass.data[DOMAIN]` instead
3. **If platform auto-discovery is interfering** — Add explicit platform registration in `__init__.py`

### After Fix

1. Run `pytest` to ensure existing tests still pass
2. Add a test for multiple percentiles being configured and verified as multiple entities
3. Test in a real Home Assistant instance with 2+ comma-separated percentiles
