"""DataUpdateCoordinator for Amber SmartShift Status."""
from __future__ import annotations

import logging
from datetime import timedelta

import cloudscraper
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, URL, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class AmberSmartShiftCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Amber SmartShift Status data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.scraper = cloudscraper.create_scraper()

    async def _async_update_data(self) -> dict:
        """Fetch data from Amber website."""
        try:
            # Run scraper in executor since it's blocking
            response = await self.hass.async_add_executor_job(
                self.scraper.get, URL
            )
            response.raise_for_status()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Amber Help Center: {err}") from err

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse the page
        data = {}
        current_battery = None
        current_issue = None
        
        # We look for all tags that might contain the structured data.
        # It seems 'strong' tags contain headings like "Tesla", "Overview of Issue:", etc.
        # Or sometimes they are just plain text in paragraphs.
        # Let's iterate over all elements in the body and extract text.
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
            text = element.get_text(separator=' ', strip=True)
            if not text:
                continue
                
            # Check if this element text looks like a battery brand header
            # Usually they are just the brand name. We can identify them if they don't contain our keywords
            lower_text = text.lower()
            if any(keyword in lower_text for keyword in [
                "overview of issue", "impact:", "first identified:", "resolved:", "last updated:"
            ]):
                if current_battery:
                    if "overview of issue" in lower_text:
                        # New issue for this battery
                        current_issue = {"status": "Issue", "overview": text}
                        data[current_battery]["issues"].append(current_issue)
                    elif current_issue:
                        if "impact:" in lower_text:
                            current_issue["impact"] = text
                        elif "first identified:" in lower_text:
                            current_issue["first_identified"] = text
                        elif "resolved:" in lower_text or "resolved on:" in lower_text:
                            current_issue["resolved"] = text
                            current_issue["status"] = "Resolved"
                        elif "updated:" in lower_text:
                            current_issue["last_updated"] = text
            else:
                # It might be a battery name if it's short and in a strong or header tag
                if len(text) < 30 and (element.name.startswith('h') or element.find('strong')):
                    # Skip common non-battery headers
                    if text not in ["Active Issues", "Resolved Issues", "SmartShift Status"]:
                        current_battery = text
                        if current_battery not in data:
                            data[current_battery] = {"issues": []}

        # Filter out batteries that don't have active issues, or mark their overall status
        for battery, info in data.items():
            active_issues = [i for i in info["issues"] if i.get("status") != "Resolved"]
            info["overall_status"] = "Issue" if active_issues else "Healthy"
            info["active_issues"] = active_issues

        return data

    async def async_get_battery_types(self) -> list[str]:
        """Fetch the available battery types for the config flow."""
        data = await self._async_update_data()
        return list(data.keys())
