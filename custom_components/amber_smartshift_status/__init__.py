"""The Amber SmartShift Status integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AmberSmartShiftCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type AmberSmartShiftConfigEntry = ConfigEntry[AmberSmartShiftCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: AmberSmartShiftConfigEntry
) -> bool:
    """Set up Amber SmartShift Status from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = AmberSmartShiftCoordinator(hass, config_entry=entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: AmberSmartShiftConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok

