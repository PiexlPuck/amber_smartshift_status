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
        [
            AmberSmartShiftSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftMessageSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftFirstReportedSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftLastUpdatedSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftDateResolvedSensor(coordinator, battery_type, entry.entry_id),
        ]
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

class AmberSmartShiftMessageSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Representation of a Amber SmartShift Error Message Sensor."""

    _attr_has_entity_name = True
    _attr_name = "Error Details"
    _attr_icon = "mdi:text-box-outline"

    def __init__(
        self,
        coordinator: AmberSmartShiftCoordinator,
        battery_type: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_error_details"
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
        if battery_data and battery_data.get("active_issues"):
            overview = battery_data["active_issues"][0].get("overview", "")
            # Truncate to 255 characters, as Home Assistant states are limited to 255 chars
            if len(overview) > 255:
                return overview[:252] + "..."
            return overview
        return "No active issues"

class AmberSmartShiftFirstReportedSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Representation of First Reported Date Sensor."""
    _attr_has_entity_name = True
    _attr_name = "First Reported"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, battery_type, entry_id) -> None:
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_first_reported"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data or {}
        battery_data = data.get(self.battery_type)
        if battery_data and battery_data.get("active_issues"):
            return battery_data["active_issues"][0].get("first_identified", "Not provided")
        return "No issues reported"

class AmberSmartShiftLastUpdatedSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Representation of Last Updated Date Sensor."""
    _attr_has_entity_name = True
    _attr_name = "Last Updated"
    _attr_icon = "mdi:update"

    def __init__(self, coordinator, battery_type, entry_id) -> None:
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_last_updated"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data or {}
        battery_data = data.get(self.battery_type)
        if battery_data and battery_data.get("active_issues"):
            return battery_data["active_issues"][0].get("last_updated", "Not provided")
        return "No issues reported"

class AmberSmartShiftDateResolvedSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Representation of Date Resolved Sensor."""
    _attr_has_entity_name = True
    _attr_name = "Date Resolved"
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator, battery_type, entry_id) -> None:
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_date_resolved"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data or {}
        battery_data = data.get(self.battery_type)
        
        # If there's an active issue, it's not resolved yet.
        if battery_data and battery_data.get("active_issues"):
            return "Not resolved yet"
            
        # If no active issues, check if there's a recently resolved issue
        if battery_data and battery_data.get("resolved_issues"):
            return battery_data["resolved_issues"][0].get("resolved", "Date not provided")
            
        return "No issues reported"

