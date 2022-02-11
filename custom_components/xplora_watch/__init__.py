""" Xplora® Watch """
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    BINARY_SENSOR_CHARGING,
    BINARY_SENSOR_SAFEZONE,
    BINARY_SENSOR_STATE,
    CONF_CHILD_PHONENUMBER,
    CONF_COUNTRY_CODE,
    CONF_PHONENUMBER,
    CONF_PASSWORD,
    CONF_SAFEZONES,
    CONF_TRACKER_SCAN_INTERVAL,
    CONF_TYPES,
    CONF_USERLANG,
    CONF_TIMEZONE,
    DATA_XPLORA,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TRACKER_WATCH,
    DOMAIN,
    SENSOR_BATTERY,
    SENSOR_XCOIN,
    SWITCH_ALARMS,
    SWITCH_SILENTS,
    TRACKER_UPDATE,
    XPLORA_CONTROLLER,
)
from pyxplora_api import pyxplora_api_async as PXA

PLATFORMS = [BINARY_SENSOR_DOMAIN, DEVICE_TRACKER, SENSOR_DOMAIN, SWITCH_DOMAIN]

SENSORS = [
    DEVICE_TRACKER_WATCH,
    BINARY_SENSOR_STATE,
    BINARY_SENSOR_SAFEZONE,
    BINARY_SENSOR_CHARGING,
    SENSOR_BATTERY,
    SENSOR_XCOIN,
    SWITCH_SILENTS,
    SWITCH_ALARMS,
]

_LOGGER = logging.getLogger(__name__)

CONTROLLER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COUNTRY_CODE): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_PHONENUMBER): cv.string,
        vol.Required(CONF_TIMEZONE): cv.time_zone,
        vol.Required(CONF_TYPES, default=SENSORS): cv.ensure_list,
        vol.Required(CONF_USERLANG): cv.string,
        vol.Optional(CONF_SAFEZONES, default="hidden"): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
        vol.Optional(CONF_TRACKER_SCAN_INTERVAL, default=TRACKER_UPDATE): cv.time_period,
        vol.Optional(CONF_CHILD_PHONENUMBER, default=[]): cv.ensure_list,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [CONTROLLER_SCHEMA]))},
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    _LOGGER.debug(f"init Xplora® Watch")
    hass.data[CONF_CHILD_PHONENUMBER] = []
    hass.data[CONF_COUNTRY_CODE] = []
    hass.data[CONF_PASSWORD] = []
    hass.data[CONF_PHONENUMBER] = []
    hass.data[CONF_SAFEZONES] = []
    hass.data[CONF_SCAN_INTERVAL] = []
    hass.data[CONF_TIMEZONE] = []
    hass.data[CONF_TRACKER_SCAN_INTERVAL] = []
    hass.data[CONF_TYPES] = []
    hass.data[CONF_USERLANG] = []
    hass.data[DATA_XPLORA] = []

    success = False
    for controller_config in config[DOMAIN]:
        success = success or await _setup_controller(hass, controller_config, config)

    return success

async def _setup_controller(hass: HomeAssistant, controller_config, config: ConfigType) -> bool:
    childPhoneNumber = controller_config[CONF_CHILD_PHONENUMBER]
    countryCode = controller_config[CONF_COUNTRY_CODE]
    phoneNumber = controller_config[CONF_PHONENUMBER]
    password = controller_config[CONF_PASSWORD]
    userlang = controller_config[CONF_USERLANG]
    timeZone = controller_config[CONF_TIMEZONE]

    _types = controller_config[CONF_TYPES]
    _LOGGER.debug(f"Entity-Types: {_types}")
    scanInterval = controller_config[CONF_SCAN_INTERVAL]
    trackerScanInterval = controller_config[CONF_TRACKER_SCAN_INTERVAL]

    _LOGGER.debug("init API-Controller")
    controller = PXA.PyXploraApi(countryCode, phoneNumber, password, userlang, timeZone)
    await controller.init_async()
    childPhoneNumber = await controller.getWatchUserID_async(childPhoneNumber)

    _LOGGER.debug(f"Xplora® Api Version: {controller.version()}")
    _LOGGER.debug(f"set Update interval: {scanInterval}")
    _LOGGER.debug(f"set Update interval Tracker: {trackerScanInterval}")
    position = len(hass.data[DATA_XPLORA])

    hass.data[CONF_CHILD_PHONENUMBER].append(childPhoneNumber)
    hass.data[CONF_COUNTRY_CODE].append(countryCode)
    hass.data[CONF_PASSWORD].append(password)
    hass.data[CONF_PHONENUMBER].append(phoneNumber)
    hass.data[CONF_SAFEZONES].append(controller_config[CONF_SAFEZONES])
    hass.data[CONF_SCAN_INTERVAL].append(scanInterval)
    hass.data[CONF_TIMEZONE].append(timeZone)
    hass.data[CONF_TRACKER_SCAN_INTERVAL].append(trackerScanInterval)
    hass.data[CONF_TYPES].append(_types)
    hass.data[CONF_USERLANG].append(userlang)
    hass.data[DATA_XPLORA].append(controller)

    if DEVICE_TRACKER_WATCH not in _types:
        PLATFORMS.remove(DEVICE_TRACKER)

    for platform in PLATFORMS:
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                platform,
                DOMAIN,
                {XPLORA_CONTROLLER: position, **controller_config},
                config,
            )
        )
    return True