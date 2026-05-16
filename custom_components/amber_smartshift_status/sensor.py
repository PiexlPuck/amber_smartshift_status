"""Sensor platform for Amber SmartShift Status."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_BATTERY_TYPE
from .coordinator import AmberSmartShiftCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    battery_type = entry.data[CONF_BATTERY_TYPE]

    async_add_entities(
        [AmberSmartShiftSensor(coordinator, battery_type, entry.entry_id)]
    )


class AmberSmartShiftSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Representation of a Amber SmartShift Status Sensor."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:battery-alert"

    def __init__(
        self,
        coordinator: AmberSmartShiftCoordinator,
        battery_type: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_status"
        # The device info links this sensor to a device in the UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": f"Amber SmartShift - {battery_type}",
            "manufacturer": "Amber Electric",
            "model": battery_type,
        }

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        data = self.coordinator.data or {}
        battery_data = data.get(self.battery_type)
        if battery_data:
            return battery_data.get("overall_status", "Healthy")
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return the state attributes."""
        data = self.coordinator.data or {}
        battery_data = data.get(self.battery_type)
        
        attributes = {
            "battery_type": self.battery_type,
        }
        
        if battery_data and "issues" in battery_data:
            # We provide the raw issues list
            attributes["all_issues"] = battery_data["issues"]
            attributes["active_issues"] = battery_data.get("active_issues", [])
            attributes["active_issue_count"] = len(battery_data.get("active_issues", []))
            
            # For easy dashboard display, we can extract the first active issue details if present
            if battery_data.get("active_issues"):
                first_issue = battery_data["active_issues"][0]
                attributes["current_issue_overview"] = first_issue.get("overview")
                attributes["current_issue_impact"] = first_issue.get("impact")
                attributes["current_issue_identified"] = first_issue.get("first_identified")

        return attributes
