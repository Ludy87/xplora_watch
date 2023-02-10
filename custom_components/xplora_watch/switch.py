"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity, SwitchEntityDescription
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
    SwitchEntityDescription(
        key=SWITCH_ALARMS,
        icon="mdi:alarm",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key=SWITCH_SILENTS,
        icon="mdi:school",
        device_class=SwitchDeviceClass.SWITCH,
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Xplora® Watch Version 2 switch from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[Any] = []

    for description in SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            if config_entry.options:
                ward: dict[str, Any] = watch.get("ward")
                wuid = ward.get(ATTR_ID, "")
                if wuid in config_entry.options.get(CONF_WATCHES, []):
                    if description.key in config_entry.options.get(CONF_TYPES, []):
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
                _LOGGER.debug(f"{watch} {config_entry.entry_id} - no config options")
    async_add_entities(entities, True)


class XploraAlarmSwitch(XploraBaseEntity, SwitchEntity):
    def __init__(
        self,
        config_entry: ConfigEntry,
        alarm: dict[str, Any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        wuid: str,
        description: SwitchEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
        self._alarm = alarm
        i = (self._options.get(CONF_WATCHES, []).index(wuid) + 1) if self._options.get(CONF_WATCHES, []) else -1
        if i == -1:
            return
        _wuid: str = self._options.get(f"{CONF_WATCHES}_{i}", "")
        if _wuid.find("=") != -1:
            friendly_name = _wuid.split("=")
            if friendly_name[0] == wuid:
                self._attr_name: str = f'{friendly_name[1]} Alarm {alarm["start"]}'.title()
            else:
                self._attr_name: str = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Alarm {alarm["start"]} {wuid}'.title()
        else:
            self._attr_name: str = f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Alarm {alarm["start"]} {wuid}'.title()

        self._attr_unique_id = f'{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-Alarm-{alarm["start"]}-{wuid}'
        self._attr_is_on = self._states(alarm["status"])
        self._alarms: list[dict[str, Any]] = []
        _LOGGER.debug(
            "Updating switch: %s | %s | Watch_ID %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
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
        alarms = await self.coordinator.controller.setEnableAlarmTime(alarmId=self._alarm[ATTR_ID])
        if alarms:
            self._attr_is_on = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        alarms = await self.coordinator.controller.setDisableAlarmTime(alarmId=self._alarm[ATTR_ID])
        if alarms:
            self._attr_is_on = False
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        language = self._options.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        week_repeat = self._alarm["weekRepeat"]
        week_days = []
        for i, day in enumerate(week_repeat):
            if week_repeat[i] == "1":
                week_days.append(DAYS.get(language, DEFAULT_LANGUAGE)[i])
        return {STR_DAYS.get(language, DEFAULT_LANGUAGE): ", ".join(week_days)}


class XploraSilentSwitch(XploraBaseEntity, SwitchEntity):
    def __init__(
        self,
        config_entry: ConfigEntry,
        silent: dict[str, Any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        wuid: str,
        description: SwitchEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
        self._silent = silent
        i = (self._options.get(CONF_WATCHES, []).index(wuid) + 1) if self._options.get(CONF_WATCHES, []) else -1
        if i == -1:
            return
        _wuid: str = self._options.get(f"{CONF_WATCHES}_{i}", "")
        if _wuid.find("=") != -1:
            friendly_name = _wuid.split("=")
            if friendly_name[0] == wuid:
                self._attr_name: str = f'{friendly_name[1]} Silent {silent["start"]}-{silent["end"]}'.title()
            else:
                self._attr_name: str = (
                    f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Silent {silent["start"]}-{silent["end"]} {wuid}'.title()
                )
        else:
            self._attr_name: str = (
                f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} Silent {silent["start"]}-{silent["end"]} {wuid}'.title()
            )

        self._attr_is_on = self._states(silent["status"])
        self._attr_unique_id = f'{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-Silent-{silent["start"]}-{silent["end"]}-{wuid}'
        _LOGGER.debug(
            "Updating switch: %s | %s | %s Watch_ID %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
            i,
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
        silents = await self.coordinator.controller.setEnableSilentTime(silentId=self._silent[ATTR_ID])
        if silents:
            self._attr_is_on = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        silents = await self.coordinator.controller.setDisableSilentTime(silentId=self._silent[ATTR_ID])
        if silents:
            self._attr_is_on = False
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        language = self._options.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        week_repeat = self._silent["weekRepeat"]
        week_days = []
        for i, day in enumerate(week_repeat):
            if week_repeat[i] == "1":
                week_days.append(DAYS.get(language, DEFAULT_LANGUAGE)[i])
        return {STR_DAYS.get(language, DEFAULT_LANGUAGE): ", ".join(week_days)}
