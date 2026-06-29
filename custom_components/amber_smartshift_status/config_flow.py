"""Config flow for Amber SmartShift Status integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import DOMAIN, CONF_BATTERY_TYPE
from .coordinator import AmberSmartShiftCoordinator

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Amber SmartShift Status."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.battery_types: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if not self.battery_types:
            try:
                coordinator = AmberSmartShiftCoordinator(self.hass)
                self.battery_types = await coordinator.async_get_battery_types()
            except Exception:
                _LOGGER.exception("Failed to fetch battery types from Amber website")
                errors["base"] = "cannot_connect"
                # Fallback to some known ones if website is down
                self.battery_types = ["Tesla", "AlphaESS", "Sungrow", "SolarEdge", "Redback", "Sigenergy", "Fronius", "1KOMMA5°", "Neovolt", "FoxESS", "Enphase", "Anker", "GivEnergy"]

        if user_input is not None:
            if not user_input[CONF_BATTERY_TYPE]:
                errors["base"] = "select_battery"
            else:
                # Check if we already have this battery type configured
                await self.async_set_unique_id(user_input[CONF_BATTERY_TYPE])
                self._abort_if_unique_id_configured()

                title = f"Amber SmartShift - {user_input[CONF_BATTERY_TYPE]}"
                return self.async_create_entry(title=title, data=user_input)

        # Remove duplicates and sort
        battery_types = sorted(list(set(self.battery_types)))

        # Format options to show a friendly select prompt at the top
        options = [{"value": "", "label": "Please select a battery..."}] + [
            {"value": b, "label": b} for b in battery_types
        ]

        schema = vol.Schema(
            {
                vol.Required(CONF_BATTERY_TYPE, default=""): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
