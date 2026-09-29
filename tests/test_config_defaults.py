"""Tests for config flow defaults — verify correct fallbacks."""

import re

from custom_components.pure_energy_prices.const import (
    CONF_ADDED_COSTS,
    CONF_GAS_ELEMENT_ID,
    CONF_RETURN_COSTS,
    DEFAULT_ADDED_COSTS,
    DEFAULT_GAS_ELEMENT_ID,
    DEFAULT_RETURN_COSTS,
    DOMAIN,
)


class TestConfigFlowDefaults:
    """Verify correct default fallbacks in config_flow.py."""

    def test_return_costs_uses_default_return_costs(self):
        """CONF_RETURN_COSTS should use DEFAULT_RETURN_COSTS as default."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        # Match CONF_RETURN_COSTS followed by its default= parameter on the next line
        pattern = r"CONF_RETURN_COSTS[^}]*?default\s*=\s*defaults\.get\(CONF_RETURN_COSTS\s*,\s*DEFAULT_(\w+)"
        match = re.search(pattern, source, re.DOTALL)
        assert match is not None, "CONF_RETURN_COSTS default not found in config_flow.py"
        assert match.group(1) == "RETURN_COSTS"

    def test_added_costs_uses_default_added_costs(self):
        """CONF_ADDED_COSTS should use DEFAULT_ADDED_COSTS as default."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        pattern = r"CONF_ADDED_COSTS[^}]*?default\s*=\s*defaults\.get\(CONF_ADDED_COSTS\s*,\s*DEFAULT_(\w+)"
        match = re.search(pattern, source, re.DOTALL)
        assert match is not None, "CONF_ADDED_COSTS default not found in config_flow.py"
        assert match.group(1) == "ADDED_COSTS"

    def test_gas_element_uses_default_gas_element(self):
        """CONF_GAS_ELEMENT_ID should use DEFAULT_GAS_ELEMENT_ID as default."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        pattern = r"CONF_GAS_ELEMENT_ID[^}]*?default\s*=\s*defaults\.get\(CONF_GAS_ELEMENT_ID\s*,\s*DEFAULT_(\w+)"
        match = re.search(pattern, source, re.DOTALL)
        assert match is not None
        assert match.group(1) == "GAS_ELEMENT_ID"

    def test_scan_interval_uses_default(self):
        """CONF_SCAN_INTERVAL should use DEFAULT_SCAN_INTERVAL as default."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        pattern = r"CONF_SCAN_INTERVAL[^}]*?default\s*=\s*defaults\.get\(CONF_SCAN_INTERVAL\s*,\s*DEFAULT_(\w+)"
        match = re.search(pattern, source, re.DOTALL)
        assert match is not None
        assert match.group(1) == "SCAN_INTERVAL"

    def test_double_meter_uses_default(self):
        """CONF_DOUBLE_METER should use DEFAULT_DOUBLE_METER as default."""
        source = open("custom_components/pure_energy_prices/config_flow.py").read()
        pattern = r"CONF_DOUBLE_METER[^}]*?default\s*=\s*defaults\.get\(CONF_DOUBLE_METER\s*,\s*DEFAULT_(\w+)"
        match = re.search(pattern, source, re.DOTALL)
        assert match is not None
        assert match.group(1) == "DOUBLE_METER"
