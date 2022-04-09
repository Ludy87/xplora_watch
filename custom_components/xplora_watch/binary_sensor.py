"""Reads Xplora® Watch status."""
from __future__ import annotations

import logging

from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription
)
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTR_WATCH,
    BINARY_SENSOR_CHARGING,
    BINARY_SENSOR_SAFEZONE,
    BINARY_SENSOR_STATE,
    CONF_TYPES,
    CONF_WATCHUSER_ID,
    DATA_XPLORA,
    XPLORA_CONTROLLER
)
from .helper import XploraUpdateTime

from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_CHARGING,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_SAFEZONE,
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_STATE,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    conf: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    if discovery_info is None:
        return
    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    watch_ids: list = hass.data[CONF_WATCHUSER_ID][discovery_info[XPLORA_CONTROLLER]]
    scan_interval: timedelta = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time: float = datetime.timestamp(datetime.now())
    _types: list = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    entities = []

    for description in BINARY_SENSOR_TYPES:
        if description.key in _types:
            _type = description.key
            for watch_id in watch_ids:
                client_name = controller.getWatchUserName(watch_id)
                entities.append(
                    XploraBinarySensor(description, controller, scan_interval, start_time, _type, watch_id, client_name)
                )
    add_entities(entities, True)


class XploraBinarySensor(XploraUpdateTime, BinarySensorEntity, RestoreEntity):

    def __init__(
        self,
        description: BinarySensorEntity,
        controller: PXA.XploraApi,
        scan_interval,
        start_time,
        _type: str,
        watch_id,
        name,
    ) -> None:
        super().__init__(scan_interval, start_time)
        self._attr_name = f"{name} {ATTR_WATCH} {_type} {watch_id}".title()
        self._attr_unique_id = f"{watch_id}_{name}_{ATTR_WATCH}_{_type}"

        self.entity_description = description
        self._controller: PXA.PyXploraApi = controller
        self._watch_id = watch_id
        self._types = _type
        _LOGGER.debug(f"set Binary Sensor: {self.entity_description.key}")

    async def __isOnline(self) -> bool:
        await self._controller.init()
        self._attr_icon = "mdi:lan-check"
        if (await self._controller.askWatchLocate(self._watch_id) is True) or (
           await self._controller.trackWatchInterval(self._watch_id) != -1):
            return True
        state = await self._controller.getWatchOnlineStatus(self._watch_id)
        if (state == "ONLINE"):
            return True
        self._attr_icon = "mdi:lan-disconnect"
        return False

    async def __isSafezone(self) -> bool:
        if await self._controller.getWatchIsInSafeZone(self._watch_id):
            return False
        return True

    async def __isCharging(self) -> bool:
        if await self._controller.getWatchIsCharging(self._watch_id):
            return True
        return False

    def __isTypes(self, sensor_type: str) -> bool:
        if sensor_type in self._types and self.entity_description.key == sensor_type:
            return True
        return False

    def __default_attr(self, fun) -> None:
        self._attr_is_on = fun

    async def __update(self) -> None:
        if self.__isTypes(BINARY_SENSOR_STATE):
            self.__default_attr(await self.__isOnline())

            _LOGGER.debug("Updating sensor: %s | State: %s", self._attr_name, str(self._attr_is_on))

        elif self.__isTypes(BINARY_SENSOR_SAFEZONE):
            self.__default_attr(await self.__isSafezone())

            _LOGGER.debug("Updating sensor: %s | State: %s", self._attr_name, str(self._attr_is_on))

        elif self.__isTypes(BINARY_SENSOR_CHARGING):
            self.__default_attr(await self.__isCharging())

            _LOGGER.debug("Updating sensor: %s | State: %s", self._attr_name, str(self._attr_is_on))

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            await self.__update()
