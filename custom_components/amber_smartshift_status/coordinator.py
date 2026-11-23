"""DataUpdateCoordinator for Amber SmartShift Status."""
from __future__ import annotations

from datetime import datetime
import logging
import re
import time
from typing import Any

from bs4 import BeautifulSoup, Tag
import cloudscraper

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CACHE_TTL_SECONDS, DOMAIN, REQUEST_TIMEOUT, SCAN_INTERVAL, URL

_LOGGER = logging.getLogger(__name__)

HEADING_AND_LABEL_TAGS = ("strong", "h1", "h2", "h3", "h4")

IGNORE_KEYWORDS = {
    "overview of issue",
    "impact",
    "first identified",
    "issue begun",
    "resolved",
    "resolved on",
    "issue resolved on",
    "last updated",
    "updated",
    "active issues",
    "current issues",
    "resolved issues",
    "archived issues",
    "about",
    "join us",
    "social",
    "comments",
    "user actions",
    "update",
    "update 1",
    "update 2",
    "beta integrations",
}


def _extract_following_text(element: Tag) -> str:
    """Extract text nodes and inline elements following a label tag up to the next label/heading."""
    parts: list[str] = []
    sibling = element.next_sibling
    while sibling and getattr(sibling, "name", "") not in HEADING_AND_LABEL_TAGS:
        if isinstance(sibling, str):
            if sibling.strip():
                parts.append(" " + sibling.strip())
        elif getattr(sibling, "name", "") == "br":
            parts.append("\n")
        elif getattr(sibling, "name", "") != "a":
            parts.append(" " + sibling.get_text(separator=" ", strip=True))
        sibling = sibling.next_sibling

    raw_text = "".join(parts)
    cleaned = re.sub(r" +", " ", raw_text).lstrip(": ").strip()
    return cleaned


def parse_status_html(html: str) -> dict[str, Any]:
    """Parse the Amber SmartShift Status HTML into structured battery status data."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(class_="article__body") or soup

    data: dict[str, Any] = {}
    current_battery: str | None = None
    current_issue: dict[str, Any] | None = None
    in_resolved_section = False

    for element in container.find_all(HEADING_AND_LABEL_TAGS):
        text = element.get_text(separator=" ", strip=True)
        if not text:
            continue

        lower_text = text.lower()

        # Break early if we hit the archived sections (only if it's a heading)
        if element.name in ("h1", "h2", "h3"):
            if "archived issues" in lower_text:
                break
            if "resolved issues" in lower_text:
                in_resolved_section = True
                current_battery = None
                current_issue = None
                continue

        # Check for issue start
        if "overview of issue" in lower_text:
            if current_battery:
                clean_overview = _extract_following_text(element)
                current_issue = {
                    "status": "Resolved" if in_resolved_section else "Issue",
                    "overview": clean_overview,
                }
                data[current_battery]["issues"].append(current_issue)
            continue

        # Check for issue fields
        if current_issue and any(
            k in lower_text
            for k in (
                "impact",
                "first identified",
                "issue begun",
                "resolved",
                "last updated",
                "updated",
            )
        ):
            clean_prop = _extract_following_text(element)

            if "impact" in lower_text:
                current_issue["impact"] = clean_prop
            elif "first identified" in lower_text or "issue begun" in lower_text:
                current_issue["first_identified"] = clean_prop
            elif "resolved" in lower_text:
                if clean_prop:
                    current_issue["resolved"] = clean_prop
                current_issue["status"] = "Resolved"
            elif "updated" in lower_text:
                current_issue["last_updated"] = clean_prop
            continue

        # Candidate battery brand header
        if len(text) < 40:
            clean_text = text.replace("✅", "").replace("⚠️", "")
            clean_text = (
                clean_text.replace("No live outages", "").replace("BETA", "").strip()
            )
            clean_lower = clean_text.lower().rstrip(":")

            if (
                clean_text
                and clean_lower not in IGNORE_KEYWORDS
                and "limitation" not in clean_lower
                and "resolved on" not in clean_lower
                and ":" not in clean_text
                and "smartshift" not in clean_lower
            ):
                current_battery = clean_text
                current_issue = None
                if current_battery not in data:
                    data[current_battery] = {"issues": []}

    # Determine active vs resolved issues for each battery
    for info in data.values():
        active_issues = [
            i for i in info["issues"] if i.get("status") != "Resolved"
        ]
        resolved_issues = [
            i for i in info["issues"] if i.get("status") == "Resolved"
        ]
        info["overall_status"] = "Issue" if active_issues else "Healthy"
        info["active_issues"] = active_issues
        info["resolved_issues"] = resolved_issues

    data["_last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return data


def _fetch_html_sync(scraper: cloudscraper.CloudScraper | None = None) -> tuple[cloudscraper.CloudScraper, str]:
    """Fetch HTML synchronously using cloudscraper."""
    if scraper is None:
        scraper = cloudscraper.create_scraper()
    response = scraper.get(URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return scraper, response.text


async def async_fetch_status_data(hass: HomeAssistant) -> dict[str, Any]:
    """Fetch and parse Amber SmartShift Status data with a short-lived shared cache."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    cached_data: dict[str, Any] | None = domain_data.get("_cached_data")
    cached_time: float = domain_data.get("_cached_time", 0.0)

    if cached_data is not None and (time.monotonic() - cached_time) < CACHE_TTL_SECONDS:
        return cached_data

    scraper: cloudscraper.CloudScraper | None = domain_data.get("_scraper")
    scraper, html = await hass.async_add_executor_job(_fetch_html_sync, scraper)
    domain_data["_scraper"] = scraper

    data = parse_status_html(html)
    domain_data["_cached_data"] = data
    domain_data["_cached_time"] = time.monotonic()
    return data


class AmberSmartShiftCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Amber SmartShift Status data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Amber website."""
        try:
            return await async_fetch_status_data(self.hass)
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Amber Help Center: {err}"
            ) from err


