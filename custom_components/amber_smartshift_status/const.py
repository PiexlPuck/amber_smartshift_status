"""Constants for the Amber SmartShift Status integration."""
from datetime import timedelta

DOMAIN = "amber_smartshift_status"
NAME = "Amber SmartShift Status"
URL = "https://help.amber.com.au/hc/en-us/articles/35922375367181-SmartShift-Status"
SCAN_INTERVAL = timedelta(minutes=30)
REQUEST_TIMEOUT = 30
CACHE_TTL_SECONDS = 60

CONF_BATTERY_TYPE = "battery_type"

DEFAULT_BATTERY_TYPES: list[str] = [
    "Fleet-wide",
    "1KOMMA5°",
    "AlphaESS",
    "Anker",
    "Enphase",
    "FoxESS",
    "Fronius",
    "GivEnergy",
    "GoodWe",
    "Neovolt",
    "Redback",
    "Sigenergy",
    "SolarEdge",
    "Sungrow",
    "Tesla",
]

