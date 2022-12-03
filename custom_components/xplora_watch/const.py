"""Const for Xplora® Watch Version 2."""
from __future__ import annotations

from typing import Final

from homeassistant.const import CONF_EMAIL

DOMAIN: Final = "xplora_watch"
MANUFACTURER: Final = "Xplora®"
DEVICE_NAME: Final = "Xplora® Watch"
ATTRIBUTION: Final = "Data provided by Xplora®"

URL_OPENSTREETMAP = "https://nominatim.openstreetmap.org/reverse?lat={}&lon={}&format=jsonv2&accept-language={}"

ATTR_SERVICE_MSG: Final = "message"
ATTR_SERVICE_SEE: Final = "see"
ATTR_SERVICE_READ_MSG: Final = "read_message"
ATTR_SERVICE_SEND_MSG: Final = "send_message"
ATTR_SERVICE_SHUTDOWN: Final = "shutdown"
ATTR_SERVICE_TARGET: Final = "target"

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
CONF_LANGUAGE: Final = "language"
CONF_MAPS: Final = "maps"
CONF_MESSAGE: Final = "message"
CONF_OPENCAGE_APIKEY: Final = "opencage_apikey"
CONF_PHONENUMBER: Final = "phonenumber"
CONF_SIGNIN_TYP: Final = "signin_typ"
CONF_TIMEZONE: Final = "timezone"
CONF_TYPES: Final = "types"
CONF_USERLANG: Final = "userlang"
CONF_WATCHES: Final = "watches"

SENSOR_BATTERY: Final = "battery"
SENSOR_DISTANCE: Final = "distance"
SENSOR_MESSAGE: Final = "message"
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

HOME: Final = "zone.home"
TRACKER_UPDATE_STR: Final = f"{DOMAIN}_tracker_update"

DATA_HASS_CONFIG: Final = "hass_config"

MAPS: Final[list[str]] = ["openstreetmap.org (free)", "opencagedata.com (with Licence)"]

##########################
# Section: Multilanguage #
##########################

DEFAULT_LANGUAGE: Final = "en"

LANGUAGES: Final[list[str]] = ["de", "en"]

STR_DAYS: Final[dict[str, str]] = {
    "en": "Day(s)",
    "de": "Tag(e)",
}

DAYS: Final[dict[str, list[str]]] = {
    "en": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "de": ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
}

HOME_SAFEZONE: Final[dict[str, dict[str, str]]] = {
    "en": {"off": "off", "on": "on"},
    "de": {"off": "aus", "on": "an"},
}

SIGNIN: Final[dict[str, dict[str, str]]] = {
    "en": {
        CONF_EMAIL: "Signed up with an email address",
        CONF_PHONENUMBER: "Signed up with a phone number",
    },
    "de": {
        CONF_EMAIL: "Mit E-Mail-Adresse angemeldet",
        CONF_PHONENUMBER: "Mit Telefonnummer angemeldet",
    },
}

SENSORS: Final[dict[str, dict[str, str]]] = {
    "en": {
        BINARY_SENSOR_CHARGING: "show charging",
        BINARY_SENSOR_SAFEZONE: "is in Safezone",
        BINARY_SENSOR_STATE: "online State",
        DEVICE_TRACKER_SAFZONES: "show Safezone",
        DEVICE_TRACKER_WATCH: "Watch tracking",
        SENSOR_BATTERY: "Battery state",
        SENSOR_DISTANCE: "Distance",
        SENSOR_MESSAGE: "Read Message(s) from Account",
        SENSOR_STEP_DAY: "Steps per Day",
        SENSOR_XCOIN: "XCoins",
        SWITCH_ALARMS: "Alarms",
        SWITCH_SILENTS: "Time of silent",
    },
    "de": {
        BINARY_SENSOR_CHARGING: "Laden anzeigen",
        BINARY_SENSOR_SAFEZONE: "ist in Sicherheitszone",
        BINARY_SENSOR_STATE: "Online Status",
        DEVICE_TRACKER_SAFZONES: "Sicherheitszone(n) anzeigen",
        DEVICE_TRACKER_WATCH: "Watch Tracking",
        SENSOR_BATTERY: "Batterie-Status",
        SENSOR_DISTANCE: "Distanz",
        SENSOR_MESSAGE: "Nachricht(en) vom Account",
        SENSOR_STEP_DAY: "Schritte pro Tag",
        SENSOR_XCOIN: "XCoins",
        SWITCH_ALARMS: "Wecker",
        SWITCH_SILENTS: "Schulzeit",
    },
}


STR_SEND_MESSAGE_SERVICE: Final[dict[str, str]] = {
    "en": """# Please do not change the file, it will be overwritten!
send_message:
  name: Send message
  description: Send a notification.
  fields:
    message:
      name: Message
      description: Message body of the notification.
      required: true
      selector:
        text:
    target:
      name: Watch
      description: Select your watch to send the message.
      required: true
      selector:
        select:
          options:
            - all
""",
    "de": """# Please do not change the file, it will be overwritten!
send_message:
  name: Nachricht senden
  description: Sende eine Benachrichtigung.
  fields:
    message:
      name: Nachricht
      description: Nachrichtentext der Benachrichtigung.
      required: true
      selector:
        text:
    target:
      name: Uhr(en)
      description: W\u00e4hle deine Uhr aus, um die Nachricht zu versenden.
      required: true
      selector:
        select:
          options:
            - all
""",
}

STR_SEE_SERVICE: Final[dict[str, str]] = {
    "en": """
see:
  name: Track Watch
  description: Manually update all information from your watch
  fields:
    target:
      name: Watch
      description: Select your watch to update data.
      required: true
      selector:
        select:
          options:
            - all
""",
    "de": """
see:
  name: Watch Tracken
  description: Aktualisiere manuell alle Informationen von deiner Uhr
  fields:
    target:
      name: Uhr(en)
      description: W\u00e4hle deine Uhr aus, um die Daten zu aktualisieren.
      required: true
      selector:
        select:
          options:
            - all
""",
}

STR_READ_MESSAGE_SERVICE: Final[dict[str, str]] = {
    "en": """
read_message:
  name: Read messages
  description: Read messages from Watch
  fields:
    target:
      name: Watch
      description: Select your watch to read the messages.
      required: true
      selector:
        select:
          options:
            - all
""",
    "de": """
read_message:
  name: Nachrichten lesen
  description: Nachrichten von Watch lesen
  fields:
    target:
      name: Uhr(en)
      description: W\u00e4hle deine Uhr aus, von der die Nachricht abgerufen werden soll.
      required: true
      selector:
        select:
          options:
            - all
""",
}

STR_SHUTDOWN_SERVICE: Final[dict[str, str]] = {
    "en": """
shutdown:
  name: Shutdown Watch
  description: Turn off the Watch
  fields:
    target:
      name: Watch
      description: Select your watch to turn off.
      required: true
      selector:
        select:
          options:
            - all
""",
    "de": """
shutdown:
  name: Uhr ausschalten
  description: Uhr herunterfahren
  fields:
    target:
      name: Uhr(en)
      description: W\u00e4hle deine Uhr aus, die ausgeschaltet werden soll.
      required: true
      selector:
        select:
          options:
            - all
""",
}
