# Plan: Fix Gas Price Including Electricity Added Costs

## Goal

Gas price sensor must NOT have electricity added costs (belasting, nettoprijs, etc.) applied or included — gas should reflect base API prices only, unlike electricity which legitimately includes surcharges.

## Current Context / Assumptions

### What the code does now
- `custom_components/pure_energy_prices/coordinator.py` line 155-158 has a condition that checks:
  - `self._commodity == CONF_COMMODITY_ELECTRICITY` before applying `added_costs` (import direction)
  - `self._commodity == CONF_COMMODITY_GAS` has NO matching branch — it falls through to `pass`
- `sensor.py` line 26 imports `CONF_ADDED_COSTS` from `const.py`, where `DEFAULT_ADDED_COSTS = 0.0`
- However, the API returns **all-inclusive** prices for BOTH electricity and gas (same price field for both)
- The "added costs" are baked into the API response for gas — they're not a separate field to add/subtract
- This means gas sensors display `price + electricity_addons` when they should display just the base price

### What's in the fixture data (`tests/fixtures/pure_energie_real_data.json`)
- Contains **electricity** data only (price: 0.3247882 kWh, with label "13:00 tot 14:00" etc.)
- Prices include: marktprijs + nettolading + stroombelasting + leveringsprijs + toeslagen
- Gas fixture data has the same structure — same `price` field, same `unity` field (kWh for elec, m³ for gas)
- The API endpoint is the same for both commodities; the `commodity` query param just filters

### Root cause
The Pure Energie API returns **all-inclusive prices** for every commodity. For electricity, those added costs are legitimate (taxes, network fees). For gas, the API **also** includes surcharges (gas taxes, delivery fees) in the same `price` field. The integration should be fine for electricity (those are real costs), but the user says gas prices should **not** include "extra electricity added costs" — suggesting the API response for gas incorrectly includes electricity surcharges, or the integration is accidentally mixing electricity's all-inclusive price with gas sensors.

### Key files involved
- `custom_components/pure_energy_prices/coordinator.py` — `_apply_cost_adjustments()` method (line ~88-125)
- `custom_components/pure_energy_prices/sensor.py` — sensor entity creation
- `custom_components/pure_energy_prices/const.py` — `DEFAULT_ADDED_COSTS = 0.0`
- `tests/test_coordinator_direction.py` — tests for import/export adjustments
- `tests/fixtures/pure_energie_real_data.json` — sample API data

## Architecture / Proposed Approach

1. **Verify the bug**: Add a gas-specific fixture to the test data, then write a failing test that asserts gas price equals raw API price (no adjustments).
2. **Fix `_apply_cost_adjustments`**: Add an explicit `elif self._commodity == CONF_COMMODITY_GAS` branch that skips all adjustments for gas.
3. **Verify existing tests still pass**: The electricity import test should still add costs, export should still subtract return costs, and the new gas test should pass.

This is a 1-line fix in `coordinator.py` plus one test. The `_apply_cost_adjustments` method already has commodity-specific branching; gas just needs an explicit "skip" branch to make the intent clear and prevent future regressions.

## Step-by-Step Tasks

### Task 1: Add gas fixture data to test fixtures

**File:** `tests/fixtures/pure_energie_real_data.json`

**Goal:** Add a gas price entry that mirrors the structure of the existing electricity data but with gas-appropriate values (m³ unit, no electricity surcharges).

**Current state:** The fixture contains only electricity price data (kWh, price ~0.32). No gas entries exist.

**Action:** Append a gas price record to the `prices` array:

```json
    {
      "price": 1.1705,
      "unity": "m³",
      "label": "00:00 tot 01:00 16 september 2026",
      "date": {
        "label": "00:00 tot 01:00 16 september 2026",
        "current": false,
        "is_past": true,
        "hour": "00:00",
        "day_name": "Wo",
        "day_number": 16,
        "month": "sep.",
        "year": "2026",
        "full": "2026-09-16 00:00"
      }
    },
    {
      "price": 1.0895,
      "unity": "m³",
      "label": null,
      "date": {
        "label": "01:00 tot 02:00 16 september 2026",
        "current": false,
        "is_past": true,
        "hour": "01:00",
        "day_name": "Wo",
        "day_number": 16,
        "month": "sep.",
        "year": "2026",
        "full": "2026-09-16 01:00"
      }
    }
```

Insert these two objects between the existing electricity entry and the closing `]` of the `prices` array.

**Expected output after change:** JSON remains valid. `jq .` on the file should parse without errors.

### Task 2: Create gas cost-adjustment test (should FAIL initially)

**File:** `tests/test_gas_cost_adjustments.py` (new file)

**Goal:** Write a test that asserts gas prices are NOT modified by `_apply_cost_adjustments`.

**Code:**
```python
"""Tests confirming gas prices are not adjusted (no added costs, no return costs)."""
import pytest
from unittest.mock import MagicMock

from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator
from custom_components.pure_energy_prices.const import (
    CONF_ADDED_COSTS,
    CONF_COMMODITY_ELECTRICITY,
    CONF_COMMODITY_GAS,
    CONF_RETURN_COSTS,
)


class TestGasNotAdjusted:
    """Gas should receive zero cost adjustments — only the raw API price."""

    def _make_coordinator(self, commodity=CONF_COMMODITY_GAS, direction="import"):
        entry = MagicMock()
        entry.data = {CONF_ADDED_COSTS: 0.02, CONF_RETURN_COSTS: 0.03}
        with patch.object(
            PureEnergyCoordinator,
            "__init__",
            lambda self, *args, **kwargs: None,
        ):
            coordinator = PureEnergyCoordinator.__new__(PureEnergyCoordinator)
            coordinator._entry = entry
            coordinator._commodity = commodity
            coordinator._direction = direction
            return coordinator

    def test_gas_import_no_added_costs_applied(self):
        """Gas import should NOT add electricity-style costs."""
        coordinator = self._make_coordinator(commodity=CONF_COMMODITY_GAS, direction="import")
        # entry.data has added_costs=0.02, but gas should not have them added
        prices = [{"price": 1.0}]
        result = coordinator._apply_cost_adjustments(prices)
        # BUG (current): if the fix is not applied, gas might get costs applied
        # EXPECTED: gas price is exactly the API price, unchanged
        assert result[0]["price"] == pytest.approx(1.0)

    def test_gas_export_no_return_costs_subtracted(self):
        """Gas export should NOT subtract return costs (gas has no export)."""
        coordinator = self._make_coordinator(commodity=CONF_COMMODITY_GAS, direction="export")
        prices = [{"price": 1.0}]
        result = coordinator._apply_cost_adjustments(prices)
        # Gas has no export; return costs should not be subtracted
        assert result[0]["price"] == pytest.approx(1.0)

    def test_gas_import_with_non_zero_added_cost(self):
        """Even when entry.data has added_costs set, gas should ignore them."""
        coordinator = self._make_coordinator(commodity=CONF_COMMODITY_GAS, direction="import")
        coordinator._entry.data[CONF_ADDED_COSTS] = 0.05  # Simulate some added cost
        prices = [{"price": 1.0}]
        result = coordinator._apply_cost_adjustments(prices)
        assert result[0]["price"] == pytest.approx(1.0)
```

**Command to run:**
```bash
cd repos/prive/hacs-pure-energy-prices
python -m pytest tests/test_gas_cost_adjustments.py -v
```

**Expected result:** Tests FAIL initially because `_apply_cost_adjustments` currently falls through without a gas-specific branch, potentially applying unwanted adjustments.

### Task 3: Fix `_apply_cost_adjustments` for gas

**File:** `custom_components/pure_energy_prices/coordinator.py`

**Current code (around lines 116-124):**
```python
        if self._direction == "import" and self._commodity == CONF_COMMODITY_ELECTRICITY and added_costs > 0:
            new_record["price"] = price + added_costs
        elif self._direction == "export":
            new_record["price"] = price - return_costs
        
        adjusted.append(new_record)
```

**Change:** Add an explicit `elif` branch for gas that does nothing (explicitly skip adjustments):

```python
        if self._direction == "import" and self._commodity == CONF_COMMODITY_ELECTRICITY and added_costs > 0:
            new_record["price"] = price + added_costs
        elif self._commodity == CONF_COMMODITY_GAS:
            # Gas prices from the API already include all applicable costs.
            # Do NOT apply electricity surcharge logic to gas.
            pass
        elif self._direction == "export":
            new_record["price"] = price - return_costs
        
        adjusted.append(new_record)
```

This makes the gas case explicit (preventing future regressions where someone might add a gas branch that incorrectly applies costs) and documents why.

### Task 4: Verify existing tests still pass

**Command:**
```bash
cd repos/prive/hacs-pure-energy-prices
python -m pytest tests/test_coordinator_direction.py tests/test_sensor_commodities.py tests/test_export_electricity.py -v
```

**Expected result:** All existing tests pass. The export tests still subtract return costs, the electricity import test still adds costs, and the gas test (from Task 2) now passes.

### Task 5: Run full test suite

**Command:**
```bash
cd repos/prive/hacs-pure-energy-prices
python -m pytest tests/ -v
```

**Expected result:** All tests pass.

### Task 6: Verify the sensor displays correctly (manual check)

After the fix, restart Home Assistant and check the gas sensor entity:
```bash
# In Home Assistant UI: Developer Tools > States
# Look for sensor.pure_energie_gas_price (or similar)
# The value should match the raw API price for gas, without any added costs
```

## Risks, Tradeoffs, and Open Questions

### Risks
1. **Fixture data mismatch:** The existing fixture (`pure_energie_real_data.json`) contains only electricity data. If the real API returns different structures for gas (different fields, different price format), the test data won't reflect reality. Verify the actual API response for gas by checking the user's Home Assistant logs or making a test API call.
2. **Gas might legitimately have costs:** Gas does have taxes (gasbelasting) and delivery fees in the Netherlands. If the user actually wants those to be visible, the fix might strip legitimate costs. Confirm with the user whether they want gas prices **completely unadjusted** (raw API price) or whether specific gas costs should be visible.
3. **Redelivery gas:** If there's a redelivery element for gas (element_id 13422), the export branch might still apply return costs. The fix explicitly blocks this for gas regardless of direction.

### Tradeoffs
- **Explicit `pass` vs. removing the else entirely:** Adding an explicit `elif self._commodity == CONF_COMMODITY_GAS: pass` makes the intent obvious and prevents regressions. An alternative would be restructuring the if/elif chain, but that's unnecessary complexity for a two-branch (electricity vs. gas) system.
- **Test fixture vs. real API:** The test uses hardcoded prices. A better approach would be to mock the API response directly, but that requires more setup. The fixture approach is simpler and sufficient for testing the cost-adjustment logic.

### Open Questions
1. **What exactly is the "extra electricity added cost" the user sees?** Is it the `CONF_ADDED_COSTS` value being applied to gas? Or is the API itself returning electricity prices for gas endpoints? Clarification from the user would help pinpoint the exact bug.
2. **Should there be gas-specific added costs?** Dutch gas has its own taxes and fees. The current `DEFAULT_ADDED_COSTS = 0.0` might be intentional (those costs are already in the API price), but we should confirm.
3. **Is there a redelivery element for gas?** The fixture has `CONF_REDELIVERY_ELEMENT_ID = "redelivery_element_id"`. If gas has redelivery sensors, the export branch's return-cost subtraction might incorrectly apply to gas. The fix blocks this for all gas directions.

## Verification Checklist

- [ ] `python -m pytest tests/test_gas_cost_adjustments.py -v` — 2 tests, both PASS
- [ ] `python -m pytest tests/test_coordinator_direction.py -v` — all PASS (export/adjustment tests)
- [ ] `python -m pytest tests/test_export_electricity.py -v` — all PASS (electricity export still works)
- [ ] `python -m pytest tests/ -v` — full suite passes, no regressions
- [ ] `python -c "from custom_components.pure_energy_prices.coordinator import PureEnergyCoordinator; print('Import OK')"` — module loads without errors
- [ ] Gas sensor in Home Assistant shows raw API price (not adjusted)
