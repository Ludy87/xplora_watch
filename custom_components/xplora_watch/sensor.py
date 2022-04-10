"""Support for reading status from Xplora® Watch."""
from __future__ import annotations

import logging

from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription
)
from homeassistant.const import CONF_SCAN_INTERVAL, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTR_WATCH,
    CONF_TYPES,
    CONF_WATCHUSER_ID,
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
    watch_ids: list = hass.data[CONF_WATCHUSER_ID][discovery_info[XPLORA_CONTROLLER]]
    scan_interval: timedelta = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time: float = datetime.timestamp(datetime.now())
    _types: list = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    entities = []

    for description in SENSOR_TYPES:
        if description.key in _types:
            _type = description.key
            for watch_id in watch_ids:
                client_name = controller.getWatchUserName(watch_id)
                entities.append(
                    XploraSensor(description, controller, scan_interval, start_time, _type, watch_id, client_name)
                )
    add_entities(entities, True)


class XploraSensor(XploraUpdateTime, SensorEntity, RestoreEntity):
    def __init__(
        self,
        description: SensorEntityDescription,
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
        _LOGGER.debug(f"set Sensor: {self.entity_description.key}")

    def __isTypes(self, sensor_type: str) -> bool:
        if sensor_type in self._types and self.entity_description.key == sensor_type:
            return True
        return False

    def __default_attr(self, fun, unit_of_measurement) -> None:
        self._attr_native_value = fun
        self._attr_unit_of_measurement = unit_of_measurement

    async def __update(self) -> None:
        """ https://github.com/home-assistant/core/blob/master/homeassistant/helpers/entity.py#L219 """

        if self.__isTypes(SENSOR_BATTERY):
            charging = await self._controller.getWatchIsCharging(watchID=self._watch_id)

            self.__default_attr((await self._controller.getWatchBattery(watchID=self._watch_id)), PERCENTAGE)
            self._attr_icon = bat(self._attr_native_value, charging)

            _LOGGER.debug(
                "Updating sensor: %s | Battery: %s | Charging %s",
                self._attr_name, str(self._attr_native_value), str(charging)
            )

        elif self.__isTypes(SENSOR_XCOIN):

            self.__default_attr(self._controller.getWatchXcoin(watchID=self._watch_id), "💰")

            _LOGGER.debug("Updating sensor: %s | XCoins: %s", self._attr_name, str(self._attr_native_value))

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            await self.__update()
