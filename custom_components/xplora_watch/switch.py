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
    SWITCH_SILENTS,
    XPLORA_CONTROLLER,
)
from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
):
    if discovery_info is None:
        return
    entities = []
    scan_interval = hass.data[CONF_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = hass.data[CONF_START_TIME][discovery_info[XPLORA_CONTROLLER]]
    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    await controller.update_a()
    _types = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]
    if SWITCH_SILENTS in _types:
        for silent in await controller.schoolSilentMode_a():
            entities.append(SilentSwitch(hass, silent, controller, scan_interval, start_time))

        add_entities(entities)

class SilentSwitch(SwitchEntity):

    def __init__(self, hass, silent: list, controller: PXA.PyXploraApi, scan_interval, start_time) -> None:
        _LOGGER.debug("init switch")
        self._hass = hass
        self._silent = silent
        self._controller: PXA.PyXploraApi = controller
        self._start_time = start_time
        self._first = True
        self._scan_interval = scan_interval
        self._state = self.__state(self._silent["status"])


    def __update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())


    def __state(self, status) -> bool:
        if status == "DISABLE":
            return False
        return True

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the device."""
        return self._silent["id"]

    @property
    def name(self):
        """Return the name of the device."""
        return f'{self._controller.getWatchUserName()} Watch Silent {self._silent["start"]}-{self._silent["end"]}'

    @property
    def is_on(self):
        """Return true if the switch is on."""
        _LOGGER.debug(f"is_on Set State {self._state}")
        return self._state

    @property
    def device_info(self):
        """Return device specific attributes."""
        return {
            "name": f'{self._controller.getWatchUserName()} Watch Silent {self._silent["start"]}-{self._silent["end"]}',
            "manufacturer": "Xplora®",
            "model": "Watch",
            "weekRepeat": self._silent['weekRepeat'],
        }

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if (await self._controller.setEnableSilentTime_a(self._silent["id"])):
            self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if (await self._controller.setDisableSilentTime_a(self._silent["id"])):
            self._state = False

    async def async_update(self) -> None:
        if self.__update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            await self._controller.update_a()
            await self._controller.askWatchLocate_a()
            for silent in await self._controller.schoolSilentMode_a():
                if silent['id'] == self._silent['id']:
                    self._state = self.__state(silent['status'])
                    _LOGGER.debug(f"newStat: {self._state} - {self.is_on}")

