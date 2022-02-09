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
    CONF_CHILD_PHONENUMBER,
    CONF_TYPES,
    DATA_XPLORA,
    SENSOR_BATTERY,
    SENSOR_XCOIN,
    XPLORA_CONTROLLER,
)
from .helper import XploraUpdateTime
from .sensor_const import bat
from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_BATTERY,
        device_class=SensorDeviceClass.BATTERY,
    ),
    SensorEntityDescription(
        key=SENSOR_XCOIN,
        icon="mdi:hand-coin"
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
    child_no = hass.data[CONF_CHILD_PHONENUMBER][discovery_info[XPLORA_CONTROLLER]]
    scan_interval = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = datetime.timestamp(datetime.now())
    _types = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    for description in SENSOR_TYPES:
        if description.key in _types:
            add_entities([
                XploraSensor(
                    description,
                    controller,
                    scan_interval,
                    start_time,
                    _types,
                    child_no)
                ], True)

class XploraSensor(SensorEntity, XploraUpdateTime):
    def __init__(
        self,
        description: SensorEntityDescription,
        controller: PXA.XploraApi,
        scan_interval,
        start_time,
        _types: str,
        child_no
    ) -> None:
        super().__init__(scan_interval, start_time)
        self.entity_description = description
        self._controller: PXA.PyXploraApi = controller
        self._types = _types
        self._child_no = child_no
        _LOGGER.debug(f"set Sensor: {self.entity_description.key}")

    async def __isTypes(self, sensor_type: str) -> bool:
        if sensor_type in self._types and self.entity_description.key == sensor_type:
            return True
        return False

    async def __default_attr(self, fun, sensor_type, unit_of_measurement, id) -> None:
        self._attr_native_value = fun
        client_name = await self._controller.getWatchUserName_async(id)
        self._attr_name = f"{client_name} {ATTR_WATCH} {sensor_type} {id}".title()
        self._attr_unique_id = f"{id}{self._attr_name}"
        self._attr_unit_of_measurement = unit_of_measurement

    async def __update(self, id) -> None:
        """ https://github.com/home-assistant/core/blob/master/homeassistant/helpers/entity.py#L219 """
        
        if await self.__isTypes(SENSOR_BATTERY):
            charging = await self._controller.getWatchIsCharging_async(id)

            await self.__default_attr((await self._controller.getWatchBattery_async(id)), SENSOR_BATTERY, PERCENTAGE, id)
            self._attr_icon = bat(self._attr_native_value, charging)

            _LOGGER.debug("Updating sensor: %s | Battery: %s | Charging %s", self._attr_name, str(self._attr_native_value), str(charging))

        elif await self.__isTypes(SENSOR_XCOIN):

            await self.__default_attr(await self._controller.getWatchXcoin_async(id), SENSOR_XCOIN, "💰", id)

            _LOGGER.debug("Updating sensor: %s | XCoins: %s", self._attr_name, str(self._attr_native_value))

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            for id in self._child_no:
                await self.__update(id)
