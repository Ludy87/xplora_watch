"""Support for reading status from Xplora® Watch."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_TYPES,
    CONF_WATCHUSER_ID,
    DATA_XPLORA,
    SWITCH_ALARMS,
    SWITCH_SILENTS,
    XPLORA_CONTROLLER,
)
from .entity import XploraSwitchEntity

from pyxplora_api import pyxplora_api_async as PXA


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
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

    for id in watch_ids:
        if SWITCH_SILENTS in _types:
            for silent in await controller.schoolSilentMode_async(id):
                name = f'{await controller.getWatchUserName_async(id)} Watch Silent {silent["start"]}-{silent["end"]} {id}'
                entities.append(SilentSwitch(silent, controller, scan_interval, start_time, name, id))
        if SWITCH_ALARMS in _types:
            for alarm in await controller.getWatchAlarm_async(id):
                name = f'{await controller.getWatchUserName_async(id)} Watch Alarm {alarm["start"]} {id}'
                entities.append(AlarmSwitch(alarm, controller, scan_interval, start_time, name, id))

    add_entities(entities)


class SilentSwitch(XploraSwitchEntity):

    def __init__(self, silent: list, controller: PXA.PyXploraApi, scan_interval, start_time, name, id) -> None:
        super().__init__(silent, controller, scan_interval, start_time, name, "silent", "mdi:school")
        self._silent = silent
        self._id = id

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if (await self._controller.setEnableSilentTime_async(self._silent["id"], self._id)):
            self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if (await self._controller.setDisableSilentTime_async(self._silent["id"], self._id)):
            self._attr_is_on = False

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            silents = await self._controller.schoolSilentMode_async(self._id)
            for silent in silents:
                if silent['id'] == self._silent['id']:
                    self._attr_is_on = self._state(silent['status'])


class AlarmSwitch(XploraSwitchEntity):

    def __init__(self, alarm: list, controller: PXA.PyXploraApi, scan_interval, start_time, name, id) -> None:
        super().__init__(alarm, controller, scan_interval, start_time, name, "alarm", "mdi:alarm")
        self._alarm = alarm
        self._id = id

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if (await self._controller.setEnableAlarmTime_async(self._alarm["id"], self._id)):
            self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if (await self._controller.setDisableAlarmTime_async(self._alarm["id"], self._id)):
            self._attr_is_on = False

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            alarms = await self._controller.getWatchAlarm_async(self._id)
            for alarm in alarms:
                if alarm['id'] == self._alarm['id']:
                    self._attr_is_on = self._state(alarm['status'])
