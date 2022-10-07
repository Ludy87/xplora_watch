"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_WATCH,
    CONF_LANGUAGE,
    CONF_TYPES,
    CONF_WATCHES,
    DAYS,
    DEFAULT_LANGUAGE,
    DOMAIN,
    STR_DAYS,
    SWITCH_ALARMS,
    SWITCH_SILENTS,
)
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
    entities: list[any] = []

    for description in SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            if config_entry.options:
                ward: dict[str, any] = watch.get("ward")
                wuid = ward.get(ATTR_ID)
                if wuid in config_entry.options.get(CONF_WATCHES):
                    if description.key in config_entry.options.get(CONF_TYPES):
                        sw_version = await coordinator.controller.getWatches(wuid)
                        if description.key == SWITCH_ALARMS:
                            for alarm in await coordinator.controller.getWatchAlarm(wuid):
                                entities.append(
                                    XploraAlarmSwitch(config_entry, alarm, coordinator, ward, sw_version, wuid, description)
                                )
                        if description.key == SWITCH_SILENTS:
                            for silent in await coordinator.controller.getSilentTime(wuid):
                                entities.append(
                                    XploraSilentSwitch(config_entry, silent, coordinator, ward, sw_version, wuid, description)
                                )
            else:
                _LOGGER.debug(f"{watch} {config_entry.entry_id}")
    async_add_entities(entities, True)


class XploraAlarmSwitch(XploraBaseEntity, SwitchEntity):

    _attr_force_update = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        alarm: dict[str, any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, any],
        sw_version: dict[str, any],
        wuid: str,
        description: SwitchEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
        self._alarm = alarm

        for i in range(1, len(self._option.get(CONF_WATCHES)) + 1):
            _wuid: str = self._option.get(f"{CONF_WATCHES}_{i}")
            if "=" in _wuid:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == wuid:
                    self._attr_name = f'{friendly_name[1]} Alarm {alarm["start"]}'.title()
                else:
                    self._attr_name = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Alarm {alarm["start"]} {wuid}'.title()
            else:
                self._attr_name = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Alarm {alarm["start"]} {wuid}'.title()

        self._attr_unique_id = f'{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-Alarm-{alarm["start"]}-{wuid}'
        self._attr_is_on = self._states(alarm["status"])
        self._alarms: list[dict[str, any]] = []
        _LOGGER.debug(
            "Updating switch: %s | %s | Watch_ID %s",
            self._attr_name[:-33] if "=" not in _wuid else self._attr_name,
            self.entity_description.key,
            self.watch_uid[25:],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for alarm in self.coordinator.data[self.watch_uid]["alarm"]:
            if alarm[ATTR_ID] == self._alarm[ATTR_ID]:
                self._attr_is_on = self._states(alarm["status"])
                self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        alarms = await self._coordinator.controller.setEnableAlarmTime(alarmId=self._alarm[ATTR_ID], wuid=self.watch_uid)
        if alarms:
            self._attr_is_on = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        alarms = await self._coordinator.controller.setDisableAlarmTime(alarmId=self._alarm[ATTR_ID], wuid=self.watch_uid)
        if alarms:
            self._attr_is_on = False
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return supported attributes."""
        language = self._option.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        weekRepeat = self._alarm["weekRepeat"]
        weekDays = []
        for day in range(len(weekRepeat)):
            if weekRepeat[day] == "1":
                weekDays.append(DAYS.get(language)[day])
        return {STR_DAYS.get(language): ", ".join(weekDays)}


class XploraSilentSwitch(XploraBaseEntity, SwitchEntity):

    _attr_force_update = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        silent: dict[str, any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, any],
        sw_version: dict[str, any],
        wuid: str,
        description: SwitchEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
        self._silent = silent
        self._silents: list[dict[str, any]] = self._coordinator.data[wuid]["silent"]

        for i in range(1, len(self._option.get(CONF_WATCHES)) + 1):
            _wuid: str = self._option.get(f"{CONF_WATCHES}_{i}")
            if "=" in _wuid:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == wuid:
                    self._attr_name = f'{friendly_name[1]} Silent {silent["start"]}-{silent["end"]}'.title()
                else:
                    self._attr_name = (
                        f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Silent {silent["start"]}-{silent["end"]} {wuid}'.title()
                    )
            else:
                self._attr_name = (
                    f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Silent {silent["start"]}-{silent["end"]} {wuid}'.title()
                )

        self._attr_is_on = self._states(silent["status"])
        self._attr_unique_id = f'{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-Silent-{silent["start"]}-{silent["end"]}-{wuid}'
        _LOGGER.debug(
            "Updating switch: %s | %s | Watch_ID %s",
            self._attr_name[:-33] if "=" not in _wuid else self._attr_name,
            self.entity_description.key,
            wuid[25:],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for silent in self.coordinator.data[self.watch_uid]["silent"]:
            if silent[ATTR_ID] == self._silent[ATTR_ID]:
                self._attr_is_on = self._states(silent["status"])
                self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        silents = await self._coordinator.controller.setEnableSilentTime(silentId=self._silent[ATTR_ID], wuid=self.watch_uid)
        if silents:
            self._attr_is_on = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        silents = await self._coordinator.controller.setDisableSilentTime(silentId=self._silent[ATTR_ID], wuid=self.watch_uid)
        if silents:
            self._attr_is_on = False
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return supported attributes."""
        language = self._option.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        weekRepeat = self._silent["weekRepeat"]
        weekDays = []
        for day in range(len(weekRepeat)):
            if weekRepeat[day] == "1":
                weekDays.append(DAYS.get(language)[day])
        return {STR_DAYS.get(language): ", ".join(weekDays)}
