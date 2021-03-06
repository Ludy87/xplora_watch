"""Support for reading status from Xplora® Watch."""
from __future__ import annotations

import logging

from datetime import datetime, timedelta
from typing import Any, Dict, List

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONF_SCAN_INTERVAL, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTR_WATCH,
    CONF_TYPES,
    CONF_WATCHUSER_ID,
    DATA_XPLORA,
    SENSOR_BATTERY,
    SENSOR_STEP_DAY,
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
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
    SensorEntityDescription(
        key=SENSOR_STEP_DAY,
        icon="mdi:run",
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_XCOIN, icon="mdi:hand-coin", native_unit_of_measurement="💰", device_class=SensorDeviceClass.MONETARY
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    conf: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if discovery_info is None:
        return
    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    watch_ids: List[str] = hass.data[CONF_WATCHUSER_ID][discovery_info[XPLORA_CONTROLLER]]
    scan_interval: timedelta = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time: float = datetime.timestamp(datetime.now())
    _types: List[str] = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    entities: List[SensorEntity] = []

    for description in SENSOR_TYPES:
        if description.key in _types:
            _type = description.key
            for watch_id in watch_ids:
                client_name = controller.getWatchUserNames(wuid=watch_id)
                entities.append(
                    XploraSensor(
                        description,
                        controller,
                        scan_interval,
                        start_time,
                        _type,
                        watch_id,
                        client_name,
                    )
                )
    add_entities(entities, True)


class XploraSensor(XploraUpdateTime, SensorEntity, RestoreEntity):
    def __init__(
        self,
        description: SensorEntityDescription,
        controller: PXA.XploraApi,
        scan_interval: timedelta,
        start_time: float,
        _type: str,
        watch_id: str,
        name: str,
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

    def __default_attr(self, fun: int) -> None:
        self._attr_native_value = fun

    async def __update(self) -> None:
        """https://github.com/home-assistant/core/blob/master/homeassistant/helpers/entity.py#L219"""

        if self.__isTypes(SENSOR_BATTERY):
            charging = await self._controller.getWatchIsCharging(wuid=self._watch_id)

            self.__default_attr((await self._controller.getWatchBattery(wuid=self._watch_id)))
            self._attr_icon = bat(self._attr_native_value, charging)

            _LOGGER.debug(
                "Updating sensor: %s | Battery: %s | Charging %s",
                self._attr_name,
                str(self._attr_native_value),
                str(charging),
            )

        elif self.__isTypes(SENSOR_STEP_DAY):

            d = datetime.now()
            dt = datetime(year=d.year, month=d.month, day=d.day)
            steps = await self._controller.getWatchUserSteps(wuid=self._watch_id, date=dt.timestamp())
            day_steps: List[Dict[str, Any]] = steps.get("daySteps", [])
            for day_step in day_steps:
                if day_step.get("key", "1970-12-31").__eq__("{}-{}-{}".format(d.year, d.strftime("%m"), d.day)):
                    self.__default_attr(day_step.get("step", 0))

            _LOGGER.debug(
                "Updating sensor: %s | Step per Day: %s",
                self._attr_name,
                str(self._attr_native_value),
            )

        elif self.__isTypes(SENSOR_XCOIN):

            self.__default_attr(self._controller.getWatchUserXcoins(wuid=self._watch_id))

            _LOGGER.debug(
                "Updating sensor: %s | XCoins: %s",
                self._attr_name,
                str(self._attr_native_value),
            )

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            await self.__update()
