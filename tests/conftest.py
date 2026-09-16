"""Fixtures for Home Assistant custom component tests."""
import pytest


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