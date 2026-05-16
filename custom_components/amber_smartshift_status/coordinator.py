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
        # Keywords to ignore as battery names
        ignore_keywords = [
            "overview of issue", "impact", "first identified", "resolved", "last updated",
            "active issues", "resolved issues", "current issues", "archived issues",
            "about", "join us", "social", "comments", "fleet-wide", "user actions", "update"
        ]

        for element in soup.find_all(['strong', 'h1', 'h2', 'h3', 'h4', 'p']):
            text = element.get_text(separator=' ', strip=True)
            if not text:
                continue
                
            lower_text = text.lower()
            
            # Check for issue fields
            if "overview of issue" in lower_text:
                if current_battery:
                    current_issue = {"status": "Issue", "overview": text}
                    data[current_battery]["issues"].append(current_issue)
                continue
            elif current_issue and any(k in lower_text for k in ["impact:", "impact", "first identified:", "resolved", "updated:"]):
                if "impact" in lower_text:
                    current_issue["impact"] = text
                elif "first identified" in lower_text:
                    current_issue["first_identified"] = text
                elif "resolved" in lower_text:
                    current_issue["resolved"] = text
                    current_issue["status"] = "Resolved"
                elif "updated:" in lower_text:
                    current_issue["last_updated"] = text
                continue
                
            # If it's short, it might be a battery brand
            if len(text) < 40 and (element.name in ['strong', 'h1', 'h2', 'h3'] or element.find('strong')):
                # Clean up text
                clean_text = text.replace('✅', '').replace('⚠️', '')
                clean_text = clean_text.replace('No live outages', '').replace('BETA', '').strip()
                
                if (clean_text and 
                    clean_text.lower() not in ignore_keywords and 
                    "limitation" not in clean_text.lower() and 
                    "resolved on" not in clean_text.lower() and
                    ":" not in clean_text and
                    "smartshift" not in clean_text.lower()):
                    
                    # Check if we already have it to avoid adding 'Overview of Issue' as a battery if logic fails
                    current_battery = clean_text
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
