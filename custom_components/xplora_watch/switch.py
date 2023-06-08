"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from pyxplora_api.pyxplora_api_async import PyXploraApi

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_LANGUAGE, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_WATCH,
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
    entities: list[any] = []

    for description in SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            options = config_entry.options
            if not options or not isinstance(watch, dict):
                _LOGGER.debug("%s %s - no config options", watch, config_entry.entry_id)
                continue

            ward: dict[str, any] = watch.get("ward", None)
            if ward is None:
                continue

            wuid = ward.get(ATTR_ID, None)
            if wuid is None:
                continue

            conf_watches = options.get(CONF_WATCHES, None)
            conf_tyes = options.get(CONF_TYPES, None)

            if conf_watches is None or conf_tyes is None or wuid not in conf_watches or description.key not in conf_tyes:
                continue

            sw_version = await coordinator.controller.getWatches(wuid)
            if description.key == SWITCH_ALARMS:
                for alarm in await coordinator.controller.getWatchAlarm(wuid):
                    entities.append(XploraAlarmSwitch(config_entry, alarm, coordinator, ward, sw_version, wuid, description))
            if description.key == SWITCH_SILENTS:
                for silent in await coordinator.controller.getSilentTime(wuid):
                    entities.append(XploraSilentSwitch(config_entry, silent, coordinator, ward, sw_version, wuid, description))

    async_add_entities(entities, True)


class XploraAlarmSwitch(XploraBaseEntity, SwitchEntity):
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
        if self.watch_uid not in self.coordinator.data:
            return
        self._watch_data: dict[str, any] = self.coordinator.data[self.watch_uid]

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
        self._alarms: list[dict[str, any]] = []
        _LOGGER.debug(
            "Updating switch: %s | Typ: %s | Watch_ID %s | state: %s | %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
            self.watch_uid[25:],
            self._attr_is_on,
            alarm["status"],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._watch_data = self.coordinator.data[self.watch_uid]
        for alarm in self._watch_data.get("alarm", []):
            if alarm[ATTR_ID] == self._alarm[ATTR_ID]:
                self._attr_is_on = self._states(alarm["status"])
                self.async_write_ha_state()
        super()._handle_coordinator_update()

    async def _set_turn_on_off(self, status: bool, **kwargs) -> None:
        controller: PyXploraApi = self.coordinator.controller
        if status:
            alarms = await controller.setEnableAlarmTime(alarm_id=self._alarm[ATTR_ID])
        else:
            alarms = await controller.setDisableAlarmTime(alarm_id=self._alarm[ATTR_ID])
        if alarms:
            self._attr_is_on = status
        await self.coordinator.init(aiohttp_client.async_create_clientsession(self.hass))
        data = self.coordinator.data
        data[self.watch_uid]["alarm"] = await self.coordinator.controller.getWatchAlarm(self.watch_uid)
        self.coordinator.data = data
        self.async_write_ha_state()
        await self.coordinator.async_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._set_turn_on_off(status=True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._set_turn_on_off(status=False)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return supported attributes."""
        language = self._options.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        week_repeat = self._alarm["weekRepeat"]
        week_days = []
        for i, _ in enumerate(week_repeat):
            if week_repeat[i] == "1":
                week_days.append(DAYS.get(language, DEFAULT_LANGUAGE)[i])
        return {STR_DAYS.get(language, DEFAULT_LANGUAGE): ", ".join(week_days)}


class XploraSilentSwitch(XploraBaseEntity, SwitchEntity):
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
        if self.watch_uid not in self.coordinator.data:
            return
        self._watch_data: dict[str, any] = self.coordinator.data[self.watch_uid]

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

        self._attr_unique_id = f'{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-Silent-{silent["start"]}-{silent["end"]}-{wuid}'
        self._attr_is_on = self._states(silent["status"])
        self._silents: list[dict[str, any]] = []
        _LOGGER.debug(
            "Updating switch: %s | Typ: %s | %s Watch_ID %s | state: %s | %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
            i,
            self.watch_uid[25:],
            self._attr_is_on,
            silent["status"],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._watch_data = self.coordinator.data[self.watch_uid]
        for silent in self._watch_data.get("silent", []):
            if silent[ATTR_ID] == self._silent[ATTR_ID]:
                self._attr_is_on = self._states(silent["status"])
                self.async_write_ha_state()
        super()._handle_coordinator_update()

    async def _set_turn_on_off(self, status: bool, **kwargs) -> None:
        controller: PyXploraApi = self.coordinator.controller
        if status:
            silents = await controller.setEnableSilentTime(silent_id=self._silent[ATTR_ID])
        else:
            silents = await controller.setDisableSilentTime(silent_id=self._silent[ATTR_ID])
        if silents:
            self._attr_is_on = status
        await self.coordinator.init(aiohttp_client.async_create_clientsession(self.hass))
        data = self.coordinator.data
        data[self.watch_uid]["silent"] = await self.coordinator.controller.getSilentTime(self.watch_uid)
        self.coordinator.data = data
        self.async_write_ha_state()
        await self.coordinator.async_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._set_turn_on_off(status=True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._set_turn_on_off(status=False)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return supported attributes."""
        language = self._options.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        week_repeat = self._silent["weekRepeat"]
        week_days = []
        for i, _ in enumerate(week_repeat):
            if week_repeat[i] == "1":
                week_days.append(DAYS.get(language, DEFAULT_LANGUAGE)[i])
        return {STR_DAYS.get(language, DEFAULT_LANGUAGE): ", ".join(week_days)}
