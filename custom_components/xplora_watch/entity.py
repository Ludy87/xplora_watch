"""Entity Xplora® Watch."""
from __future__ import annotations

import logging

from typing import Any

from .helper import XploraUpdateTime
from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)

class XploraSwitchEntity(XploraUpdateTime):
    def __init__(self, switch, controller, scan_interval, start_time, name, func_name) -> None:
        super().__init__(scan_interval, start_time)
        _LOGGER.debug(f"init switch {func_name} {name}")
        self._controller: PXA.PyXploraApi = controller
        self._switch = switch
        self._name = name
        self._attr_is_on = self._state(self._switch["status"])

    def _state(self, status) -> bool:
        if status == "DISABLE":
            return False
        return True

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the device."""
        return self._switch["id"]

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        days = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
        weekRepeat = self._switch['weekRepeat']
        weekDays = []
        for day in range(len(weekRepeat)):
            if weekRepeat[day] == "1":
                weekDays.append(days[day])
        return { "Day(s)": ', '.join(weekDays) }
