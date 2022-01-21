"""Support for reading status from Xplora® Watch."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.switch import (
    SwitchEntity
)
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_START_TIME,
    CONF_TYPES,
    DATA_XPLORA,
    SWITCH_ALARMS,
    SWITCH_SILENTS,
    XPLORA_CONTROLLER,
)
from .entity import XploraSwitchEntity
from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    if discovery_info is None:
        return
    entities = []
    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    scan_interval = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = hass.data[CONF_START_TIME][discovery_info[XPLORA_CONTROLLER]]
    _types = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    if SWITCH_SILENTS in _types:
        for silent in await controller.schoolSilentMode_async():
            name = f'{await controller.getWatchUserName_async()} Watch Silent {silent["start"]}-{silent["end"]}'
            entities.append(SilentSwitch(silent, controller, scan_interval, start_time, name))
    if SWITCH_ALARMS in _types:
        for alarm in await controller.getWatchAlarm_async():
            name = f'{await controller.getWatchUserName_async()} Watch Alarm {alarm["start"]}'
            entities.append(AlarmSwitch(alarm, controller, scan_interval, start_time, name))

    add_entities(entities)

class SilentSwitch(XploraSwitchEntity, SwitchEntity):

    def __init__(self, silent: list, controller: PXA.PyXploraApi, scan_interval, start_time, name) -> None:
        _LOGGER.debug("init switch silent")
        self._controller: PXA.PyXploraApi = controller
        self._first = True
        self._silent = silent
        self._attr_is_on = self.__state(self._silent["status"])
        self._start_time = start_time
        self._scan_interval = scan_interval
        super().__init__(self._silent, name)

    def __update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())

    def __state(self, status) -> bool:
        if status == "DISABLE":
            return False
        return True

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if (await self._controller.setEnableSilentTime_async(self._silent["id"])):
            self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if (await self._controller.setDisableSilentTime_async(self._silent["id"])):
            self._attr_is_on = False

    async def async_update(self) -> None:
        if self.__update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            silents = await self._controller.schoolSilentMode_async()
            for silent in silents:
                if silent['id'] == self._silent['id']:
                    self._attr_is_on = self.__state(silent['status'])

class AlarmSwitch(XploraSwitchEntity, SwitchEntity):

    def __init__(self, alarm: list, controller: PXA.PyXploraApi, scan_interval, start_time, name) -> None:
        _LOGGER.debug("init switch alarm")
        self._alarm = alarm
        self._controller: PXA.PyXploraApi = controller
        self._first = True
        self._attr_is_on = self.__state(self._alarm["status"])
        self._scan_interval = scan_interval
        self._start_time = start_time
        super().__init__(self._alarm, name)

    def __update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())

    def __state(self, status) -> bool:
        if status == "DISABLE":
            return False
        return True

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if (await self._controller.setEnableAlarmTime_async(self._alarm["id"])):
            self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if (await self._controller.setDisableAlarmTime_async(self._alarm["id"])):
            self._attr_is_on = False

    async def async_update(self) -> None:
        if self.__update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            alarms = await self._controller.getWatchAlarm_async()
            for alarm in alarms:
                if alarm['id'] == self._alarm['id']:
                    self._attr_is_on = self.__state(alarm['status'])
