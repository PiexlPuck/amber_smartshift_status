"""Sensor platform for Amber SmartShift Status."""
from __future__ import annotations

from typing import Any

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

    # Order matches user preference: Status, First Reported, Last Updated,
    # Date Resolved, Error Details, Last Polled
    async_add_entities(
        [
            AmberSmartShiftSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftFirstReportedSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftLastUpdatedSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftDateResolvedSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftMessageSensor(coordinator, battery_type, entry.entry_id),
            AmberSmartShiftLastPolledSensor(coordinator, battery_type, entry.entry_id),
        ]
    )


def _get_battery_data(coordinator, battery_type) -> dict | None:
    """Safely get battery data, returning None if coordinator data is unavailable."""
    if coordinator.data is None:
        return None
    return coordinator.data.get(battery_type)


class AmberSmartShiftSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Representation of the main Amber SmartShift Status Sensor.

    Shows 'Healthy' (green) or 'Issue' (red) based on active issues.
    """

    _attr_has_entity_name = True
    _attr_name = "Status"

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
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": f"Amber SmartShift - {battery_type}",
            "manufacturer": "Amber Electric",
            "model": battery_type,
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self) -> str | None:
        battery_data = _get_battery_data(self.coordinator, self.battery_type)
        if battery_data:
            return battery_data.get("overall_status", "Healthy")
        return None

    @property
    def icon(self) -> str:
        """Return green check or red alert icon based on status."""
        battery_data = _get_battery_data(self.coordinator, self.battery_type)
        if battery_data and battery_data.get("overall_status") == "Issue":
            return "mdi:alert-circle"
        return "mdi:check-circle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        battery_data = _get_battery_data(self.coordinator, self.battery_type)
        attributes = {"battery_type": self.battery_type}

        if battery_data and "issues" in battery_data:
            attributes["active_issues"] = battery_data.get("active_issues", [])
            attributes["active_issue_count"] = len(battery_data.get("active_issues", []))
            if battery_data.get("active_issues"):
                active_issues = battery_data["active_issues"]
                attributes["current_issue_overview"] = "\n\n".join(
                    [str(issue.get("overview", "")) for issue in active_issues]
                )
                attributes["current_issue_impact"] = "\n\n".join(
                    [str(issue.get("impact", "")) for issue in active_issues if issue.get("impact")]
                )
                attributes["current_issue_identified"] = " / ".join(
                    [str(issue.get("first_identified", "")) for issue in active_issues]
                )

        return attributes


class AmberSmartShiftFirstReportedSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Shows when the current active issue was first identified."""

    _attr_has_entity_name = True
    _attr_name = "First Reported"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, battery_type, entry_id) -> None:
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_first_reported"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self) -> str | None:
        battery_data = _get_battery_data(self.coordinator, self.battery_type)
        if battery_data and battery_data.get("active_issues"):
            active_issues = battery_data["active_issues"]
            dates = [str(issue.get("first_identified", "Not provided")) for issue in active_issues]
            return " / ".join(dates)
        return "No issues reported"


class AmberSmartShiftLastUpdatedSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Shows when the current active issue was last updated by Amber."""

    _attr_has_entity_name = True
    _attr_name = "Last Updated"
    _attr_icon = "mdi:update"

    def __init__(self, coordinator, battery_type, entry_id) -> None:
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_last_updated"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self) -> str | None:
        battery_data = _get_battery_data(self.coordinator, self.battery_type)
        if battery_data and battery_data.get("active_issues"):
            active_issues = battery_data["active_issues"]
            dates = [str(issue.get("last_updated", "Not provided")) for issue in active_issues]
            return " / ".join(dates)
        return "No issues reported"


class AmberSmartShiftDateResolvedSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Shows the resolution date of the most recent issue."""

    _attr_has_entity_name = True
    _attr_name = "Date Resolved"
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator, battery_type, entry_id) -> None:
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_date_resolved"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self) -> str | None:
        battery_data = _get_battery_data(self.coordinator, self.battery_type)

        # Active issue means not yet resolved
        if battery_data and battery_data.get("active_issues"):
            return "Not resolved yet"

        # Check most recent resolved issue
        if battery_data and battery_data.get("resolved_issues"):
            return battery_data["resolved_issues"][0].get("resolved", "Date not provided")

        return "No issues reported"


class AmberSmartShiftMessageSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Shows the full error description for the current active issue."""

    _attr_has_entity_name = True
    _attr_name = "Error Details"
    _attr_icon = "mdi:text-box-outline"

    def __init__(
        self,
        coordinator: AmberSmartShiftCoordinator,
        battery_type: str,
        entry_id: str,
    ) -> None:
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
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self) -> str | None:
        battery_data = _get_battery_data(self.coordinator, self.battery_type)
        active_issues = battery_data.get("active_issues") if battery_data else None
        if active_issues:
            # Join all active issues overviews, separated by two newlines
            overviews = [str(issue.get("overview", "Active issue reported")) for issue in active_issues]
            overview_text = "\n\n".join(overviews)
            if len(overview_text) > 255:
                return overview_text[:252] + "..."
            return overview_text
        return "No active issues"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose full untruncated overview in attributes for dashboard use."""
        battery_data = _get_battery_data(self.coordinator, self.battery_type)
        if battery_data and battery_data.get("active_issues"):
            active_issues = battery_data["active_issues"]
            return {
                "full_overview": "\n\n".join(
                    [str(issue.get("overview", "")) for issue in active_issues]
                ),
                "impact": "\n\n".join(
                    [str(issue.get("impact", "")) for issue in active_issues if issue.get("impact")]
                ),
            }
        return {}


class AmberSmartShiftLastPolledSensor(CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity):
    """Shows the timestamp of the last successful data fetch from Amber."""

    _attr_has_entity_name = True
    _attr_name = "Last Polled"
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator, battery_type, entry_id) -> None:
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_last_polled"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def native_value(self) -> str | None:
        """Return the timestamp of the last successful data fetch.

        This sensor intentionally stays available even when other sensors
        go unavailable, so you can always see when the last poll was.
        """
        if self.coordinator.data is not None:
            return self.coordinator.data.get("_last_checked", "Unknown")
        return "Never"
