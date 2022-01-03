import logging

LOGGER = logging.getLogger(__package__)

DOMAIN = "xplora_watch"
#ENTITY_ID_FORMAT = DOMAIN + ".{}"

#WATCH_UPDATE = f"{DOMAIN}_watch_update"

#PLATFORMS = ["binary_sensor", "device_tracker", "sensor", "lock"]

#ATTR_BATTERY = "battery"
#ATTR_CHARGING = "charging"
#ATTR_ICON = "icon"
ATTR_WATCH = "watch"
#ATTR_WATCH_NAME = "watch_name"

CONF_SCAN_INTERVAL = "scan_interval"
CONF_COUNTRY_CODE = "country_code"
CONF_PHONENUMBER = "phonenumber"
CONF_PASSWORD = "password"
CONF_USERLANG = "userlang"
CONF_TIMEZONE = "timezone"

XPLORA_CONTROLLER = "controller"
SENSOR_TYPE_BATTERY_SENSOR = "battery"
SENSOR_TYPE_XCOIN_SENSOR = "xcoin"

CONF_TYPES = "sensors"

DATA_XPLORA = "xplorar"

ICON_BATTERY = [
    "mdi:battery", "mdi:battery-90", "mdi:battery-80", "mdi:battery-70", "mdi:battery-60",
    "mdi:battery-50", "mdi:battery-40", "mdi:battery-30", "mdi:battery-20", "mdi:battery-10", 
    "mdi:battery-alert",
    "mdi:battery-charging-100", "mdi:battery-charging-90", "mdi:battery-charging-80", "mdi:battery-charging-70", "mdi:battery-charging-60",
    "mdi:battery-charging-50", "mdi:battery-charging-40", "mdi:battery-charging-30", "mdi:battery-charging-20", "mdi:battery-charging-10",
    ]