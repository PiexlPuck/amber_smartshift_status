"""Constants for the Amber SmartShift Status integration."""
from datetime import timedelta

DOMAIN = "amber_smartshift_status"
NAME = "Amber SmartShift Status"
URL = "https://help.amber.com.au/hc/en-us/articles/35922375367181-SmartShift-Status"
SCAN_INTERVAL = timedelta(minutes=15)

CONF_BATTERY_TYPE = "battery_type"
