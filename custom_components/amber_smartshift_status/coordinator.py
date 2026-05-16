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
        self.scraper = None

    def _fetch_data(self) -> str:
        """Fetch data synchronously."""
        if self.scraper is None:
            self.scraper = cloudscraper.create_scraper()
        response = self.scraper.get(URL)
        response.raise_for_status()
        return response.text

    async def _async_update_data(self) -> dict:
        """Fetch data from Amber website."""
        try:
            # Run scraper in executor since it's blocking
            html = await self.hass.async_add_executor_job(self._fetch_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Amber Help Center: {err}") from err

        soup = BeautifulSoup(html, 'html.parser')
        
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
            "active issues", "current issues", "archived issues",
            "about", "join us", "social", "comments", "user actions", "update",
            "update 1", "update 2"
        ]

        for element in soup.find_all(['strong', 'h1', 'h2', 'h3', 'h4']):
            text = element.get_text(separator=' ', strip=True)
            if not text:
                continue
                
            lower_text = text.lower()
            
            # Break early if we hit the resolved or archived sections (only if it's a heading)
            if element.name in ['h1', 'h2', 'h3'] and ("resolved issues" in lower_text or "archived issues" in lower_text):
                break
            
            # Check for issue fields
            if "overview of issue" in lower_text:
                if current_battery:
                    # extract the actual text following this strong tag
                    issue_text = ""
                    sibling = element.next_sibling
                    while sibling and getattr(sibling, 'name', '') not in ['strong', 'h1', 'h2', 'h3', 'h4']:
                        if isinstance(sibling, str):
                            if sibling.strip():
                                issue_text += " " + sibling.strip()
                        elif sibling.name == 'br':
                            issue_text += "\n"
                        elif sibling.name != 'a':
                            issue_text += " " + sibling.get_text(separator=' ', strip=True)
                        sibling = sibling.next_sibling
                        
                    import re
                    clean_overview = re.sub(r' +', ' ', issue_text).strip()
                    current_issue = {"status": "Issue", "overview": clean_overview}
                    data[current_battery]["issues"].append(current_issue)
                continue
            elif current_issue and any(k in lower_text for k in ["impact:", "impact", "first identified:", "resolved", "updated:"]):
                # extract text for these too
                prop_text = ""
                sibling = element.next_sibling
                while sibling and getattr(sibling, 'name', '') not in ['strong', 'h1', 'h2', 'h3', 'h4']:
                    if isinstance(sibling, str):
                        if sibling.strip():
                            prop_text += " " + sibling.strip()
                    elif sibling.name == 'br':
                        prop_text += "\n"
                    elif sibling.name != 'a':
                        prop_text += " " + sibling.get_text(separator=' ', strip=True)
                    sibling = sibling.next_sibling
                    
                import re
                clean_prop = re.sub(r' +', ' ', prop_text).strip()
                    
                if "impact" in lower_text:
                    current_issue["impact"] = clean_prop
                elif "first identified" in lower_text:
                    current_issue["first_identified"] = clean_prop
                elif "resolved" in lower_text:
                    current_issue["resolved"] = clean_prop
                    current_issue["status"] = "Resolved"
                elif "updated:" in lower_text:
                    current_issue["last_updated"] = clean_prop
                continue
                
            # If it's short, it might be a battery brand
            if len(text) < 40:
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
