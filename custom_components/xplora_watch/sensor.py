"""Support for reading status from Xplora® Watch."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription
)
from homeassistant.const import CONF_SCAN_INTERVAL, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTR_WATCH,
    CONF_COUNTRY_CODE,
    CONF_PASSWORD,
    CONF_PHONENUMBER,
    CONF_START_TIME,
    CONF_TIMEZONE,
    CONF_TYPES,
    CONF_USERLANG,
    DATA_XPLORA,
    XPLORA_CONTROLLER,
    SENSOR_TYPE_BATTERY_SENSOR,
    SENSOR_TYPE_XCOIN_SENSOR,
)
from .sensor_const import bat
from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_TYPE_BATTERY_SENSOR,
        device_class=SensorDeviceClass.BATTERY,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_XCOIN_SENSOR,
        icon="mdi:hand-coin"
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
    controller = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    await controller.update_a()
    _types = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    for description in SENSOR_TYPES:
        if description.key in _types:
            add_entities([
                XploraSensor(
                    hass,
                    description,
                    controller,
                    scan_interval,
                    start_time,
                    _types,
                    _conf) #for description in SENSOR_TYPES
                ], True)

class XploraSensor(SensorEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        description: SensorEntityDescription,
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
        self.hass = hass
        _LOGGER.debug(f"set Sensor: {self.entity_description.key}")

    def __update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())

    async def __isTypes(self, sensor_type: str) -> bool:
        self._controller.update_a()
        state = await self._controller.getWatchOnlineStatus_a()
        if (state != "ONLINE"):
            _LOGGER.debug(state)
        if sensor_type in self._types and self.entity_description.key == sensor_type:
            return True
        return False

    def __default_attr(self, fun, sensor_type, unit_of_measurement) -> None:
        self._attr_native_value = fun
        client_name = self._controller.getWatchUserName()
        self._attr_name = f"{client_name} {ATTR_WATCH} {sensor_type}".title()
        self._attr_unique_id = f"{self._controller.getWatchUserID()}{self._attr_name}"
        self._attr_unit_of_measurement = unit_of_measurement

    async def __update(self) -> None:
        """ https://github.com/home-assistant/core/blob/master/homeassistant/helpers/entity.py#L219 """
        
        if await self.__isTypes(SENSOR_TYPE_BATTERY_SENSOR):
            charging = await self._controller.getWatchIsCharging_a()

            self.__default_attr((await self._controller.getWatchBattery_a()), SENSOR_TYPE_BATTERY_SENSOR, PERCENTAGE)
            self._attr_icon = bat(self._attr_native_value, charging)

            _LOGGER.debug("Updating sensor: %s | Battery: %s | Charging %s", self._attr_name, str(self._attr_native_value), str(charging))

        elif await self.__isTypes(SENSOR_TYPE_XCOIN_SENSOR):

            self.__default_attr(self._controller.getWatchXcoin(), SENSOR_TYPE_XCOIN_SENSOR, "💰")

            _LOGGER.debug("Updating sensor: %s | XCoins: %s", self._attr_name, str(self._attr_native_value))

    async def async_update(self) -> None:
        if self.__update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            await self.__update()
