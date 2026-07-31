"""Button platform for Amber SmartShift Status."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_BATTERY_TYPE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    battery_type = entry.data[CONF_BATTERY_TYPE]

    # Only add the button if this is the Fleet-wide integration
    if battery_type == "Fleet-wide":
        async_add_entities([AmberSmartShiftHelpButton(entry.entry_id)])


class AmberSmartShiftHelpButton(ButtonEntity):
    """Button to launch/open the Amber SmartShift status webpage."""

    _attr_has_entity_name = True
    _attr_name = "Launch Web Page"
    _attr_icon = "mdi:open-in-new"

    def __init__(self, entry_id: str) -> None:
        """Initialize the button."""
        self._attr_unique_id = f"{entry_id}_fleet_wide_help_page"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Amber SmartShift - Fleet-wide",
            "manufacturer": "Amber Electric",
            "model": "Fleet-wide",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        url = "https://help.amber.com.au/hc/en-us/articles/35922375367181-SmartShift-Status"
        # Since backend cannot open user client browsers, create a persistent notification with the link
        self.hass.components.persistent_notification.async_create(
            title="Amber SmartShift Status Page",
            message=f"[Click here to view progress and status on the Amber website]({url})",
            notification_id="amber_smartshift_status_launch",
        )
