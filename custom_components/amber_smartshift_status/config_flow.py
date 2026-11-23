"""Config flow for Amber SmartShift Status integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow as HAConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_BATTERY_TYPE, DEFAULT_BATTERY_TYPES, DOMAIN
from .coordinator import async_fetch_status_data

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(HAConfigFlow, domain=DOMAIN):
    """Handle a config flow for Amber SmartShift Status."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()
        self.battery_types: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if not self.battery_types:
            try:
                data = await async_fetch_status_data(self.hass)
                self.battery_types = [k for k in data if not k.startswith("_")]
            except Exception:
                _LOGGER.exception("Failed to fetch battery types from Amber website")
                errors["base"] = "cannot_connect"
                self.battery_types = list(DEFAULT_BATTERY_TYPES)

        if user_input is not None:
            selected_battery = user_input.get(CONF_BATTERY_TYPE, "")
            if not selected_battery:
                errors["base"] = "select_battery"
            else:
                await self.async_set_unique_id(selected_battery)
                self._abort_if_unique_id_configured()

                title = f"Amber SmartShift - {selected_battery}"
                return self.async_create_entry(title=title, data=user_input)

        # Remove duplicates and sort, keeping Fleet-wide at the top if present
        unique_types = set(self.battery_types)
        has_fleet_wide = "Fleet-wide" in unique_types
        unique_types.discard("Fleet-wide")
        battery_types = (
            (["Fleet-wide"] if has_fleet_wide else []) + sorted(unique_types)
        )

        options: list[SelectOptionDict] = [
            SelectOptionDict(value="", label="Please select a battery..."),
            *[SelectOptionDict(value=b, label=b) for b in battery_types],
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

