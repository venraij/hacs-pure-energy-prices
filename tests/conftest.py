"""Fixtures for Home Assistant custom component tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


@pytest.fixture(name="bypass_load_limit", autouse=True)
def bypass_load_limit_fixture():
    """Bypass the 10% load limit during testing."""
    import os
    os.environ["HASS_LOAD_LIMIT"] = "100"
    yield


@pytest.fixture(name="mock_entry")
def mock_entry_fixture():
    """Mock a ConfigEntry."""
    from homeassistant.config_entries import ConfigEntry

    class MockConfigEntry(ConfigEntry):
        """Mock config entry."""

        def __init__(self, **kwargs):
            self._data = kwargs.get("data", {})
            self.entry_id = kwargs.get("entry_id", "test_entry")
            self.unique_id = kwargs.get("unique_id", None)
            self.version = kwargs.get("version", 1)
            self.minor_version = kwargs.get("minor_version", 0)
            self.source = kwargs.get("source", "user")
            self.title = kwargs.get("title", "Test")
            self.options = kwargs.get("options", {})
            self.subentries_data = ()
            self.disabled_by = None
            self.pref_disable_never_loaded = False
            self.entry_type = None
            self.environment_friendly = True
            self.is_honeypot = False

        @property
        def data(self):
            """Return config entry data."""
            return self._data

    yield MockConfigEntry


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry with default settings."""
    from homeassistant.config_entries import ConfigEntry
    
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        "electricity": True,
        "solar_panels": False,
        "gas": False,
        "percentiles": "0.05,0.1,0.2,0.4",
    }
    entry.options = {}
    entry.unique_id = "test_unique_id"
    return entry


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with test data."""
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.data = MagicMock()
    coordinator.data.prices = [
        {"price": 0.25, "start": "2024-01-01T00:00", "end": "2024-01-01T01:00"},
        {"price": 0.30, "start": "2024-01-01T01:00", "end": "2024-01-01T02:00"},
        {"price": 0.35, "start": "2024-01-01T02:00", "end": "2024-01-01T03:00"},
    ]
    return coordinator


@pytest.fixture
def mock_hass(mock_config_entry, mock_coordinator):
    """Create a mock Home Assistant instance."""
    from custom_components.pure_energy_prices.const import DOMAIN
    
    hass = MagicMock()
    hass.data = {}
    
    # Setup async mocks
    hass.config_entries = MagicMock()
    hass.config_entries.async_setup = AsyncMock(return_value=True)
    hass.config_entries.async_unload = AsyncMock(return_value=True)
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    
    hass.states = MagicMock()
    hass.states.entity_ids = MagicMock(return_value=[])
    hass.states.get = MagicMock(return_value=None)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "electricity_import": mock_coordinator
    }
    return hass
