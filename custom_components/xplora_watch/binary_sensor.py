"""Reads Xplora® Watch status."""
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
    BINARY_SENSOR_CHARGING,
    BINARY_SENSOR_SAFEZONE,
    BINARY_SENSOR_STATE,
    CONF_COUNTRY_CODE,
    CONF_PASSWORD,
    CONF_PHONENUMBER,
    CONF_START_TIME,
    CONF_TIMEZONE,
    CONF_TYPES,
    CONF_USERLANG,
    DATA_XPLORA,
    XPLORA_CONTROLLER
)
from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_STATE,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_SAFEZONE,
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_CHARGING,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
)

async def async_setup_platform(
    hass: HomeAssistant,
    conf: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
):
    if discovery_info is None:
        return
    scan_interval = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = hass.data[CONF_START_TIME][discovery_info[XPLORA_CONTROLLER]]
    _conf = {
        'cc': hass.data[CONF_COUNTRY_CODE][discovery_info[XPLORA_CONTROLLER]],
        'phoneNumber': hass.data[CONF_PHONENUMBER][discovery_info[XPLORA_CONTROLLER]],
        'password': hass.data[CONF_PASSWORD][discovery_info[XPLORA_CONTROLLER]],
        'userlang': hass.data[CONF_USERLANG][discovery_info[XPLORA_CONTROLLER]],
        'tz': hass.data[CONF_TIMEZONE][discovery_info[XPLORA_CONTROLLER]],
    }
    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    _types = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    for description in BINARY_SENSOR_TYPES:
        if description.key in _types:
            add_entities([
                XploraBinarySensor(
                    hass,
                    description,
                    controller,
                    scan_interval,
                    start_time,
                    _types,
                    _conf) #for description in BINARY_SENSOR_TYPES
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
        self._controller: PXA.PyXploraApi = controller
        self._start_time = start_time
        self._first = True
        self._scan_interval = scan_interval
        self._types = _types
        self._conf = _conf
        _LOGGER.debug(f"set Binary Sensor: {self.entity_description.key}")

    def __update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())

    async def __isOnline(self) -> bool:
        await self._controller.init_async()
        self._attr_icon = "mdi:lan-check"
        if (await self._controller.askWatchLocate_async() == True) or (await self._controller.trackWatchInterval_async() != -1):
            return True
        state = await self._controller.getWatchOnlineStatus_async()
        if (state == "ONLINE"):
            return True
        self._attr_icon = "mdi:lan-disconnect"
        return False

    async def __isSafezone(self) -> bool:
        if await self._controller.getWatchIsInSafeZone_async():
            return False
        return True

    async def __isCharging(self) -> bool:
        if await self._controller.getWatchIsCharging_async():
            return True
        return False

    async def __isTypes(self, sensor_type: str) -> bool:
        if sensor_type in self._types and self.entity_description.key == sensor_type:
            return True
        return False

    async def __default_attr(self, fun, sensor_type) -> None:
        self._attr_native_value = fun
        client_name = await self._controller.getWatchUserName_async()
        self._attr_name = f"{client_name} {ATTR_WATCH} {sensor_type}".title()
        self._attr_unique_id = f"{await self._controller.getWatchUserID_async()}{self._attr_name}"
        self._attr_is_on = fun

    async def __update(self) -> None:
        if await self.__isTypes(BINARY_SENSOR_STATE):
            await self.__default_attr((await self.__isOnline()), BINARY_SENSOR_STATE)

            _LOGGER.debug("Updating sensor: %s | State: %s", self._attr_name, str(self._attr_is_on))

        elif await self.__isTypes(BINARY_SENSOR_SAFEZONE):
            await self.__default_attr((await self.__isSafezone()), BINARY_SENSOR_SAFEZONE)

            _LOGGER.debug("Updating sensor: %s | State: %s", self._attr_name, str(self._attr_is_on))

        elif await self.__isTypes(BINARY_SENSOR_CHARGING):
            await self.__default_attr((await self.__isCharging()), BINARY_SENSOR_CHARGING)

            _LOGGER.debug("Updating sensor: %s | State: %s", self._attr_name, str(self._attr_is_on))

    async def async_update(self) -> None:
        if self.__update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            await self.__update()
