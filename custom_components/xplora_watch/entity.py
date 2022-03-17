"""Entity Xplora® Watch."""
from __future__ import annotations

import logging

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .helper import XploraUpdateTime

from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)


class XploraSwitchEntity(XploraUpdateTime, SwitchEntity, RestoreEntity):
    def __init__(self, switch, controller, scan_interval, start_time, name, func_name, icon) -> None:
        super().__init__(scan_interval, start_time)
        _LOGGER.debug(f"init switch {func_name} {name}")
        self._controller: PXA.PyXploraApi = controller
        self._switch = switch
        self._attr_icon = icon
        self._attr_is_on = self._state(self._switch["status"])
        self._attr_name = name
        self._attr_unique_id = switch["id"]

    def _state(self, status) -> bool:
        if status == "DISABLE":
            return False
        return True

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

