"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging

from .const import ATTR_WATCH, CONF_TYPES, CONF_WATCHES, DAYS, DOMAIN, SWITCH_ALARMS, SWITCH_SILENTS
from .coordinator import XploraDataUpdateCoordinator
from .entity import XploraBaseEntity

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(key=SWITCH_ALARMS, icon="mdi:alarm"),
    SwitchEntityDescription(key=SWITCH_SILENTS, icon="mdi:school"),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Xplora® Watch Version 2 switch from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[Any] = []

    for description in SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            if config_entry.options:
                ward: dict[str, Any] = watch.get("ward")
                uid = ward.get(ATTR_ID)
                if uid in config_entry.options.get(CONF_WATCHES):
                    if description.key in config_entry.options.get(CONF_TYPES):
                        sw_version = await coordinator.controller.getWatches(uid)
                        if description.key == SWITCH_ALARMS:
                            for alarm in await coordinator.controller.getWatchAlarm(uid):
                                entities.append(
                                    XploraAlarmSwitch(config_entry, alarm, coordinator, ward, sw_version, uid, description)
                                )
                        if description.key == SWITCH_SILENTS:
                            for silent in await coordinator.controller.getSilentTime(uid):
                                entities.append(
                                    XploraSilentSwitch(config_entry, silent, coordinator, ward, sw_version, uid, description)
                                )
            else:
                _LOGGER.debug(f"{watch} {config_entry.entry_id}")
    async_add_entities(entities, True)


class XploraAlarmSwitch(XploraBaseEntity, SwitchEntity):

    _attr_force_update = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        alarm,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        uid,
        description,
    ) -> None:
        super().__init__(coordinator, ward, sw_version, uid)
        self._alarm = alarm
        self.entity_description = description

        for i in range(1, len(config_entry.options.get(CONF_WATCHES)) + 1):
            _wuid: str = config_entry.options.get(f"{CONF_WATCHES}_{i}")
            if "=" in _wuid:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == uid:
                    self._attr_name = f'{friendly_name[1]} Alarm {alarm["start"]}'.title()
                else:
                    self._attr_name = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Alarm {alarm["start"]} {uid}'.title()
            else:
                self._attr_name = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Alarm {alarm["start"]} {uid}'.title()

        self._attr_unique_id = f'{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-Alarm-{alarm["start"]}-{uid}'
        self._watch_id = uid
        self._attr_is_on = self._states(alarm["status"])
        self._alarms: list[dict[str, Any]] = []
        _LOGGER.debug(
            "Updating switch: %s | %s | Watch_ID %s",
            self._attr_name[:-33] if "=" not in _wuid else self._attr_name,
            self.entity_description.key,
            self.watch_uid[25:],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for alarm in self.coordinator.data[self._watch_id]["alarm"]:
            if alarm[ATTR_ID] == self._alarm[ATTR_ID]:
                self._attr_is_on = self._states(alarm["status"])
                self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        alarms = await self._coordinator.controller.setEnableAlarmTime(alarmId=self._alarm[ATTR_ID], wuid=self._watch_id)
        if alarms:
            self._attr_is_on = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        alarms = await self._coordinator.controller.setDisableAlarmTime(alarmId=self._alarm[ATTR_ID], wuid=self._watch_id)
        if alarms:
            self._attr_is_on = False
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        weekRepeat = self._alarm["weekRepeat"]
        weekDays = []
        for day in range(len(weekRepeat)):
            if weekRepeat[day] == "1":
                weekDays.append(DAYS[day])
        return {"Day(s)": ", ".join(weekDays)}


class XploraSilentSwitch(XploraBaseEntity, SwitchEntity):

    _attr_force_update = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        silent,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        uid,
        description,
    ) -> None:
        super().__init__(coordinator, ward, sw_version, uid)
        self._silent = silent
        self.entity_description = description
        self._silents: list[dict[str, Any]] = self._coordinator.data[self.watch_uid]["silent"]

        for i in range(1, len(config_entry.options.get(CONF_WATCHES)) + 1):
            _wuid: str = config_entry.options.get(f"{CONF_WATCHES}_{i}")
            if "=" in _wuid:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == uid:
                    self._attr_name = f'{friendly_name[1]} Silent {silent["start"]}-{silent["end"]}'.title()
                else:
                    self._attr_name = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Silent {silent["start"]}-{silent["end"]} {self.watch_uid}'.title()
            else:
                self._attr_name = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Silent {silent["start"]}-{silent["end"]} {self.watch_uid}'.title()

        self._attr_is_on = self._states(silent["status"])
        self._attr_unique_id = f'{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-Silent-{silent["start"]}-{silent["end"]}-{uid}'
        self._watch_id = uid
        _LOGGER.debug(
            "Updating switch: %s | %s | Watch_ID %s",
            self._attr_name[:-33] if "=" not in _wuid else self._attr_name,
            self.entity_description.key,
            self.watch_uid[25:],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for silent in self.coordinator.data[self._watch_id]["silent"]:
            if silent[ATTR_ID] == self._silent[ATTR_ID]:
                self._attr_is_on = self._states(silent["status"])
                self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        silents = await self._coordinator.controller.setEnableSilentTime(silentId=self._silent[ATTR_ID], wuid=self._watch_id)
        if silents:
            self._attr_is_on = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        silents = await self._coordinator.controller.setDisableSilentTime(silentId=self._silent[ATTR_ID], wuid=self._watch_id)
        if silents:
            self._attr_is_on = False
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        weekRepeat = self._silent["weekRepeat"]
        weekDays = []
        for day in range(len(weekRepeat)):
            if weekRepeat[day] == "1":
                weekDays.append(DAYS[day])
        return {"Day(s)": ", ".join(weekDays)}
