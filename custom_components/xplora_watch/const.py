"""Const for Xplora® Watch Version 2."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "xplora_watch_2"
MANUFACTURER: Final = "Xplora®"
DEVICE_NAME: Final = "Xplora® Watch"
ATTRIBUTION: Final = "Data provided by Xplora®"

ATTR_TRACKER_ADDR: Final = "address"
ATTR_TRACKER_DISTOHOME: Final = "Home Distance (m)"
ATTR_TRACKER_IMEI: Final = "imei"
ATTR_TRACKER_LAST_TRACK: Final = "last tracking"
ATTR_TRACKER_LAT: Final = "lat"
ATTR_TRACKER_LICENCE: Final = "licence"
ATTR_TRACKER_LNG: Final = "lng"
ATTR_TRACKER_POI: Final = "poi"
ATTR_TRACKER_RAD: Final = "rad"

ATTR_WATCH: Final = "watch"

CONF_COUNTRY_CODE: Final = "country_code"
CONF_HOME_SAFEZONE: Final = "home_is_safezone"
CONF_HOME_LATITUDE: Final = "home_latitude"
CONF_HOME_LONGITUDE: Final = "home_longitude"
CONF_HOME_RADIUS: Final = "home_radius"
CONF_MAPS: Final = "maps"
CONF_OPENCAGE_APIKEY: Final = "opencage_apikey"
CONF_PHONENUMBER: Final = "phonenumber"
CONF_TIMEZONE: Final = "timezone"
CONF_TYPES: Final = "types"
CONF_USERLANG: Final = "userlang"
CONF_WATCHES: Final = "watches"

DAYS: Final = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
HOME: Final = "zone.home"

SENSOR_BATTERY: Final = "battery"
SENSOR_STEP_DAY: Final = "step_day"
SENSOR_XCOIN: Final = "xcoin"

BINARY_SENSOR_CHARGING: Final = "charging"
BINARY_SENSOR_SAFEZONE: Final = "safezone"
BINARY_SENSOR_STATE: Final = "state"

SWITCH_ALARMS: Final = "alarms"
SWITCH_SILENTS: Final = "silents"

DEVICE_TRACKER_SAFZONES: Final = "watch_safezone"
DEVICE_TRACKER_WATCH: Final = "dt_watch"

DEFAULT_SCAN_INTERVAL: Final = 3 * 60
TRACKER_UPDATE: Final = 60

TRACKER_UPDATE_STR: Final = f"{DOMAIN}_tracker_update"

DATA_HASS_CONFIG: Final = "hass_config"

HOME_SAFEZONE: Final[dict[str, str]] = {"off": "off", "on": "on"}
MAPS: Final[list[str]] = ["openstreetmap.org (free)", "opencagedata.com (with Licence)"]
SENSORS: Final[dict[str, str]] = {
    BINARY_SENSOR_CHARGING: "show charging",
    BINARY_SENSOR_SAFEZONE: "is in Safezone",
    BINARY_SENSOR_STATE: "online State",
    DEVICE_TRACKER_SAFZONES: "show Safezone",
    DEVICE_TRACKER_WATCH: "Device tracking",
    SENSOR_BATTERY: "Battery state",
    SENSOR_STEP_DAY: "Step per Day",
    SENSOR_XCOIN: "XCoins",
    SWITCH_ALARMS: "Alarms",
    SWITCH_SILENTS: "Time of silent",
}
