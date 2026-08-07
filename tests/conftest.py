"""Configuration for tests."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

import pytest


@pytest.fixture(name="config_entry")
def mock_config_entry():
    """Create a MockConfigEntry with default configuration."""
    entry = MockConfigEntry(
        domain="pure_energy_prices",
        title="Pure Energie Prices",
        data={
            "element_id": 11480,
            "double_meter": True,
            "solar_panels": True,
            "business": False,
            "horizon_hours": 24,
            "added_costs": 0.0,
            "return_costs": 0.0,
            "commodity": "electricity",
            "unit_of_measurement": "€/kWh",
            "scan_interval": 3600,
            "percentiles": [0.05, 0.1, 0.2, 0.4],
        },
        version=1,
    )
    entry.add_to_hass(mock_hass)  # type: ignore[arg-type]
    return entry


@pytest.fixture(name="config_entry_with_none_percentiles")
def mock_config_entry_none_percentiles():
    """Create a MockConfigEntry with None percentiles."""
    entry = MockConfigEntry(
        domain="pure_energy_prices",
        title="Pure Energie Prices",
        data={
            "element_id": 11480,
            "double_meter": True,
            "solar_panels": True,
            "business": False,
            "horizon_hours": 24,
            "added_costs": 0.0,
            "return_costs": 0.0,
            "commodity": "electricity",
            "unit_of_measurement": "€/kWh",
            "scan_interval": 3600,
            "percentiles": None,
        },
        version=1,
    )
    entry.add_to_hass(mock_hass)  # type: ignore[arg-type]
    return entry


@pytest.fixture(name="config_entry_empty_percentiles_list")
def mock_config_entry_empty_percentiles():
    """Create a MockConfigEntry with an empty percentiles list."""
    entry = MockConfigEntry(
        domain="pure_energy_prices",
        title="Pure Energie Prices",
        data={
            "element_id": 11480,
            "double_meter": True,
            "solar_panels": True,
            "business": False,
            "horizon_hours": 24,
            "added_costs": 0.0,
            "return_costs": 0.0,
            "commodity": "electricity",
            "unit_of_measurement": "€/kWh",
            "scan_interval": 3600,
            "percentiles": [],
        },
        version=1,
    )
    entry.add_to_hass(mock_hass)  # type: ignore[arg-type]
    return entry


@pytest.fixture(name="mock_api_response")
def mock_api_response():
    """Return a valid API response payload."""
    return {
        "prices": [
            {
                "price": 0.25,
                "date": {
                    "full": "2024-01-01 00:00",
                    "current": True,
                },
            },
            {
                "price": 0.30,
                "date": {
                    "full": "2024-01-01 01:00",
                    "current": False,
                },
            },
            {
                "price": 0.28,
                "date": {
                    "full": "2024-01-01 02:00",
                    "current": False,
                },
            },
        ],
    }


@pytest.fixture(name="mock_api_response_48h")
def mock_api_response_48h():
    """Return a 48-hour API response payload."""
    return {
        "prices": [
            {
                "price": 0.25,
                "date": {
                    "full": "2024-01-01 00:00",
                    "current": True,
                },
            },
            {
                "price": 0.30,
                "date": {
                    "full": "2024-01-01 01:00",
                    "current": False,
                },
            },
            {
                "price": 0.28,
                "date": {
                    "full": "2024-01-01 02:00",
                    "current": False,
                },
            },
            # Next day prices (hour 25-48 range)
            {
                "price": 0.20,
                "date": {
                    "full": "2024-01-02 00:00",
                    "current": False,
                },
            },
            {
                "price": 0.22,
                "date": {
                    "full": "2024-01-02 01:00",
                    "current": False,
                },
            },
        ],
    }


@pytest.fixture(name="mock_api_response_empty")
def mock_api_response_empty():
    """Return an API response with no prices."""
    return {"prices": []}


@pytest.fixture(name="config_entry_different_unit")
def mock_config_entry_gas():
    """Create a MockConfigEntry for gas (m³ unit)."""
    entry = MockConfigEntry(
        domain="pure_energy_prices",
        title="Pure Energie Prices",
        data={
            "element_id": 11480,
            "double_meter": True,
            "solar_panels": True,
            "business": False,
            "horizon_hours": 24,
            "added_costs": 0.0,
            "return_costs": 0.0,
            "commodity": "gas",
            "unit_of_measurement": "€/m³",
            "scan_interval": 3600,
            "percentiles": [0.05, 0.5],
        },
        version=1,
    )
    entry.add_to_hass(mock_hass)  # type: ignore[arg-type]
    return entry


@pytest.fixture(name="config_entry_no_added_costs")
def mock_config_entry_no_costs():
    """Create a MockConfigEntry with no added/return costs."""
    entry = MockConfigEntry(
        domain="pure_energy_prices",
        title="Pure Energie Prices",
        data={
            "element_id": 11480,
            "double_meter": True,
            "solar_panels": True,
            "business": False,
            "horizon_hours": 24,
            "added_costs": 0.0,
            "return_costs": 0.0,
            "commodity": "electricity",
            "unit_of_measurement": "€/kWh",
            "scan_interval": 3600,
            "percentiles": [0.05],
        },
        version=1,
    )
    entry.add_to_hass(mock_hass)  # type: ignore[arg-type]
    return entry


@pytest.fixture(name="config_entry_with_added_costs")
def mock_config_entry_with_costs():
    """Create a MockConfigEntry with added and return costs."""
    entry = MockConfigEntry(
        domain="pure_energy_prices",
        title="Pure Energie Prices",
        data={
            "element_id": 11480,
            "double_meter": True,
            "solar_panels": True,
            "business": False,
            "horizon_hours": 24,
            "added_costs": 0.05,
            "return_costs": 0.02,
            "commodity": "electricity",
            "unit_of_measurement": "€/kWh",
            "scan_interval": 3600,
            "percentiles": [0.1],
        },
        version=1,
    )
    entry.add_to_hass(mock_hass)  # type: ignore[arg-type]
    return entry
