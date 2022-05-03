"""Support for reading status from Xplora® Watch."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

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
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if discovery_info is None:
        return
    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    watch_ids: List[str] = hass.data[CONF_WATCHUSER_ID][discovery_info[XPLORA_CONTROLLER]]
    scan_interval: timedelta = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time: float = datetime.timestamp(datetime.now())
    _types: List[str] = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    entities = []

    for watch_id in watch_ids:
        if SWITCH_SILENTS in _types:
            for silent in await controller.getSilentTime(wuid=watch_id):
                name = (
                    f'{controller.getWatchUserNames(wuid=watch_id)} Watch Silent {silent["start"]}-{silent["end"]} {watch_id}'
                )
                entities.append(SilentSwitch(silent, controller, scan_interval, start_time, name, watch_id))
        if SWITCH_ALARMS in _types:
            for alarm in await controller.getWatchAlarm(wuid=watch_id):
                name = f'{controller.getWatchUserNames(wuid=watch_id)} Watch Alarm {alarm["start"]} {watch_id}'
                entities.append(AlarmSwitch(alarm, controller, scan_interval, start_time, name, watch_id))

    add_entities(entities)


class SilentSwitch(XploraSwitchEntity):
    def __init__(
        self,
        silent: Dict[str, Any],
        controller: PXA.PyXploraApi,
        scan_interval: timedelta,
        start_time: float,
        name: str,
        watch_id: str,
    ) -> None:
        super().__init__(silent, controller, scan_interval, start_time, name, "silent", "mdi:school")
        self._silent = silent
        self._watch_id = watch_id

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if await self._controller.setEnableSilentTime(silentId=self._silent["id"], wuid=self._watch_id):
            self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if await self._controller.setDisableSilentTime(silentId=self._silent["id"], wuid=self._watch_id):
            self._attr_is_on = False

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            silents = await self._controller.getSilentTime(wuid=self._watch_id)
            for silent in silents:
                if silent["id"] == self._silent["id"]:
                    self._attr_is_on = self._state(silent["status"])


class AlarmSwitch(XploraSwitchEntity):
    def __init__(
        self,
        alarm: Dict[str, Any],
        controller: PXA.PyXploraApi,
        scan_interval: timedelta,
        start_time: float,
        name: str,
        watch_id: str,
    ) -> None:
        super().__init__(alarm, controller, scan_interval, start_time, name, "alarm", "mdi:alarm")
        self._alarm = alarm
        self._watch_id = watch_id

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if await self._controller.setEnableAlarmTime(alarmId=self._alarm["id"], wuid=self._watch_id):
            self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if await self._controller.setDisableAlarmTime(alarmId=self._alarm["id"], wuid=self._watch_id):
            self._attr_is_on = False

    async def async_update(self) -> None:
        if self._update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            alarms = await self._controller.getWatchAlarm(wuid=self._watch_id)
            for alarm in alarms:
                if alarm["id"] == self._alarm["id"]:
                    self._attr_is_on = self._state(alarm["status"])
