from homeassistant.core import HomeAssistant

DOMAIN = "pure_energy_custom"

async def async_setup(hass: HomeAssistant, config):
    # Actual setup is done in sensor.py via async_setup_entry pattern,
    # but for a simple example we’ll register via async_setup_platform-like behavior.
    return True
