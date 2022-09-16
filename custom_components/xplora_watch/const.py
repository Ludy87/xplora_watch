"""Const for Xplora® Watch Version 2."""
DOMAIN = "xplora_watch"
MANUFACTURER = "Xplora®"
DEVICE_NAME = "Xplora® Watch"
ATTRIBUTION = "Data provided by Xplora®"

ATTR_TRACKER_ADDR = "address"
ATTR_TRACKER_DISTOHOME = "Home Distance (m)"
ATTR_TRACKER_IMEI = "imei"
ATTR_TRACKER_LAST_TRACK = "last tracking"
ATTR_TRACKER_LAT = "lat"
ATTR_TRACKER_LATITUDE = "latitude"
ATTR_TRACKER_LICENCE = "licence"
ATTR_TRACKER_LNG = "lng"
ATTR_TRACKER_LONGITUDE = "longitude"
ATTR_TRACKER_POI = "poi"
ATTR_TRACKER_RAD = "rad"

ATTR_WATCH = "watch"

CONF_COUNTRY_CODE = "country_code"
CONF_HOME_SAFEZONE = "home_is_safezone"
CONF_HOME_LATITUDE = "home_latitude"
CONF_HOME_LONGITUDE = "home_longitude"
CONF_HOME_RADIUS = "home_radius"
CONF_MAPS = "maps"
CONF_OPENCAGE_APIKEY = "opencage_apikey"
CONF_PASSWORD = "password"
CONF_PHONENUMBER = "phonenumber"
CONF_TIMEZONE = "timezone"
CONF_TYPES = "types"
CONF_USERLANG = "userlang"
CONF_WATCHES = "watches"

DAYS = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
HOME = "zone.home"

SENSOR_BATTERY = "battery"
SENSOR_STEP_DAY = "step_day"
SENSOR_XCOIN = "xcoin"

BINARY_SENSOR_CHARGING = "charging"
BINARY_SENSOR_SAFEZONE = "safezone"
BINARY_SENSOR_STATE = "state"

SWITCH_ALARMS = "alarms"
SWITCH_SILENTS = "silents"

DEVICE_TRACKER_SAFZONES = "watch_safezone"
DEVICE_TRACKER_WATCH = "dt_watch"

DEFAULT_SCAN_INTERVAL = 3 * 60
TRACKER_UPDATE = 60

TRACKER_UPDATE_STR = f"{DOMAIN}_tracker_update"

DATA_HASS_CONFIG = "hass_config"

HOME_SAFEZONE = {"no": "no", "yes": "yes"}
MAPS = ["openstreetmap.org (free)", "opencagedata.com (with Licence)"]
SENSORS = {
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
