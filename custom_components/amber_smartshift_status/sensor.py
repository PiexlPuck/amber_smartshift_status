"""Sensor platform for Amber SmartShift Status."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_BATTERY_TYPE, DOMAIN, URL
from .coordinator import AmberSmartShiftCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: AmberSmartShiftCoordinator = (
        getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    )
    battery_type: str = entry.data[CONF_BATTERY_TYPE]

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


def _get_device_info(entry_id: str, battery_type: str) -> DeviceInfo:
    """Get DeviceInfo dataclass for Amber SmartShift Status entities (HA 2026.11+ compatible)."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=f"Amber SmartShift - {battery_type}",
        manufacturer="Amber Electric",
        model=battery_type,
        configuration_url=URL,
    )


class AmberSmartShiftBaseSensor(
    CoordinatorEntity[AmberSmartShiftCoordinator], SensorEntity
):
    """Base sensor class for Amber SmartShift Status entities."""

    _attr_has_entity_name = True
    _unique_id_suffix: str

    def __init__(
        self,
        coordinator: AmberSmartShiftCoordinator,
        battery_type: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.battery_type = battery_type
        self._attr_unique_id = f"{entry_id}_{battery_type}_{self._unique_id_suffix}"
        self._attr_device_info = _get_device_info(entry_id, battery_type)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def _battery_data(self) -> dict[str, Any] | None:
        """Safely get battery data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.battery_type)


class AmberSmartShiftSensor(AmberSmartShiftBaseSensor):
    """Representation of the main Amber SmartShift Status Sensor.

    Shows 'Healthy' (green) or 'Issue' (red) based on active issues.
    """

    _attr_name = "Status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Healthy", "Issue"]
    _unique_id_suffix = "status"

    @property
    def native_value(self) -> str | None:
        """Return the overall status."""
        if battery_data := self._battery_data:
            return battery_data.get("overall_status", "Healthy")
        return None

    @property
    def icon(self) -> str:
        """Return green check or red alert icon based on status."""
        if (battery_data := self._battery_data) and battery_data.get("overall_status") == "Issue":
            return "mdi:alert-circle"
        return "mdi:check-circle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes about active issues."""
        battery_data = self._battery_data
        attributes: dict[str, Any] = {"battery_type": self.battery_type}

        if battery_data and "issues" in battery_data:
            active_issues = battery_data.get("active_issues", [])
            attributes["active_issues"] = active_issues
            attributes["active_issue_count"] = len(active_issues)
            if active_issues:
                attributes["current_issue_overview"] = "\n\n".join(
                    str(issue.get("overview", "")) for issue in active_issues
                )
                attributes["current_issue_impact"] = "\n\n".join(
                    str(issue.get("impact", ""))
                    for issue in active_issues
                    if issue.get("impact")
                )
                attributes["current_issue_identified"] = " / ".join(
                    str(issue.get("first_identified", "")) for issue in active_issues
                )

        return attributes


class AmberSmartShiftFirstReportedSensor(AmberSmartShiftBaseSensor):
    """Shows when the current active issue was first identified."""

    _attr_name = "First Reported"
    _attr_icon = "mdi:calendar-clock"
    _unique_id_suffix = "first_reported"

    @property
    def native_value(self) -> str:
        """Return when active issues were first identified."""
        if (battery_data := self._battery_data) and (
            active_issues := battery_data.get("active_issues")
        ):
            dates = [
                str(issue.get("first_identified", "Not provided"))
                for issue in active_issues
            ]
            return " / ".join(dates)
        return "No issues reported"


class AmberSmartShiftLastUpdatedSensor(AmberSmartShiftBaseSensor):
    """Shows when the current active issue was last updated by Amber."""

    _attr_name = "Last Updated"
    _attr_icon = "mdi:update"
    _unique_id_suffix = "last_updated"

    @property
    def native_value(self) -> str:
        """Return when active issues were last updated."""
        if (battery_data := self._battery_data) and (
            active_issues := battery_data.get("active_issues")
        ):
            dates = [
                str(issue.get("last_updated", "Not provided"))
                for issue in active_issues
            ]
            return " / ".join(dates)
        return "No issues reported"


class AmberSmartShiftDateResolvedSensor(AmberSmartShiftBaseSensor):
    """Shows the resolution date of the most recent issue."""

    _attr_name = "Date Resolved"
    _attr_icon = "mdi:calendar-check"
    _unique_id_suffix = "date_resolved"

    @property
    def native_value(self) -> str:
        """Return the resolution date of the latest resolved issue."""
        battery_data = self._battery_data

        # Active issue means not yet resolved
        if battery_data and battery_data.get("active_issues"):
            return "Not resolved yet"

        # Check most recent resolved issue with a resolution/update date
        if battery_data and (resolved_issues := battery_data.get("resolved_issues")):
            for issue in resolved_issues:
                if resolved_date := (issue.get("resolved") or issue.get("last_updated")):
                    return str(resolved_date)
            return "Date not provided"

        return "No issues reported"


class AmberSmartShiftMessageSensor(AmberSmartShiftBaseSensor):
    """Shows the full error description for the current active issue."""

    _attr_name = "Error Details"
    _attr_icon = "mdi:text-box-outline"
    _unique_id_suffix = "error_details"

    @property
    def native_value(self) -> str:
        """Return the active issue overview (truncated to 255 chars for HA state)."""
        if (battery_data := self._battery_data) and (
            active_issues := battery_data.get("active_issues")
        ):
            overviews = [
                str(issue.get("overview", "Active issue reported"))
                for issue in active_issues
            ]
            overview_text = "\n\n".join(overviews)
            if len(overview_text) > 255:
                return overview_text[:252] + "..."
            return overview_text
        return "No active issues"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose full untruncated overview in attributes for dashboard use."""
        if (battery_data := self._battery_data) and (
            active_issues := battery_data.get("active_issues")
        ):
            return {
                "full_overview": "\n\n".join(
                    str(issue.get("overview", "")) for issue in active_issues
                ),
                "impact": "\n\n".join(
                    str(issue.get("impact", ""))
                    for issue in active_issues
                    if issue.get("impact")
                ),
            }
        return {}


class AmberSmartShiftLastPolledSensor(AmberSmartShiftBaseSensor):
    """Shows the timestamp of the last successful data fetch from Amber."""

    _attr_name = "Last Polled"
    _attr_icon = "mdi:clock-check-outline"
    _unique_id_suffix = "last_polled"

    @property
    def available(self) -> bool:
        """Stay available even when a poll fails so the last successful poll time remains visible."""
        return True

    @property
    def native_value(self) -> str:
        """Return the timestamp of the last successful data fetch."""
        if self.coordinator.data is not None:
            return str(self.coordinator.data.get("_last_checked", "Unknown"))
        return "Never"

