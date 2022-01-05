"""Reads Xplor® Watch status."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription
)
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTR_WATCH,
    BINARY_SENSOR_STATE,
    CONF_COUNTRY_CODE,
    CONF_PASSWORD,
    CONF_PHONENUMBER,
    CONF_TIMEZONE,
    CONF_TYPES,
    CONF_USERLANG,
    DATA_XPLORA,
    XPLORA_CONTROLLER
)
from pyxplora_api import pyxplora_api as PXA

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_STATE,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)

def setup_platform(
    hass: HomeAssistant,
    conf: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
):
    if discovery_info is None:
        return
    scan_interval = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = hass.data["start_time"][discovery_info[XPLORA_CONTROLLER]]
    _conf = {
        'cc': hass.data[CONF_COUNTRY_CODE][discovery_info[XPLORA_CONTROLLER]],
        'phoneNumber': hass.data[CONF_PHONENUMBER][discovery_info[XPLORA_CONTROLLER]],
        'password': hass.data[CONF_PASSWORD][discovery_info[XPLORA_CONTROLLER]],
        'userlang': hass.data[CONF_USERLANG][discovery_info[XPLORA_CONTROLLER]],
        'tz': hass.data[CONF_TIMEZONE][discovery_info[XPLORA_CONTROLLER]],
    }
    controller = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    _types = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    _LOGGER.debug(f"Sensor: {_types}")
    add_entities([
        XploraBinarySensor(
            hass,
            description,
            controller,
            scan_interval,
            start_time,
            _types,
            _conf) for description in BINARY_SENSOR_TYPES
        ], True)

class XploraBinarySensor(BinarySensorEntity):

    def __init__(
        self,
        hass: HomeAssistant,
        description: BinarySensorEntity,
        controller: PXA.XploraApi,
        scan_interval,
        start_time,
        _types: str,
        _conf
    ):
        self.entity_description = description
        self._controller = controller
        self._start_time = start_time
        self._scan_interval = scan_interval
        self._types = _types
        self._conf = _conf
        _LOGGER.debug(f"set Sensor: {self.entity_description.key}")
        self.__update()

    def __update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())

    def __isOnline(self) -> bool:
        state = self._controller.getWatchOnlineStatus()
        if (state == "ONLINE"):
            self._controller.update()
            self._attr_icon = "mdi:lan-check"
            return True
        self._attr_icon = "mdi:lan-disconnect"
        return False

    def __update(self) -> None:
        _LOGGER.debug("update controller")
        if self.entity_description.key == BINARY_SENSOR_STATE:
            
            client_name = self._controller.getWatchUserName()
            self._attr_name = f"{client_name} {ATTR_WATCH} {BINARY_SENSOR_STATE}".title()
            self._attr_unique_id = f"{self._controller.getWatchUserID()}{self._attr_name}"
            self._attr_is_on = self.__isOnline()

    def update(self) -> None:
        if self.__update_timer():
            self._start_time = datetime.timestamp(datetime.now())
            self.__update()
