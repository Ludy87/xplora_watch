"""Reads watch status from Xplora® Watch Version 2."""

from __future__ import annotations

import logging
from typing import Any

from pyxplora_api.pyxplora_api_async import PyXploraApi

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_LANGUAGE, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_SERVICE_USER,
    ATTR_WATCH,
    CONF_TYPES,
    CONF_WATCHES,
    DAYS,
    DEFAULT_LANGUAGE,
    DOMAIN,
    STR_DAYS,
    SWITCH_ALARM,
    SWITCH_SILENT,
)
from .coordinator import XploraDataUpdateCoordinator
from .entity import XploraBaseEntity

_LOGGER = logging.getLogger(__name__)

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key=SWITCH_ALARM,
        icon="mdi:alarm",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key=SWITCH_SILENT,
        icon="mdi:school",
        device_class=SwitchDeviceClass.SWITCH,
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Xplora® Watch Version 2 switch from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[Any] = []

    for description in SWITCH_TYPES:
        for watch in coordinator.controller.watchs:
            options = config_entry.options
            if not options or not isinstance(watch, dict):
                _LOGGER.debug("%s %s - no config options", watch, config_entry.entry_id)
                continue

            ward: dict[str, Any] = watch.get("ward", None)
            if ward is None:
                continue

            wuid = ward.get(ATTR_ID, None)
            if wuid is None:
                continue

            conf_watches = options.get(CONF_WATCHES, None)
            conf_tyes = options.get(CONF_TYPES, None)

            if (
                conf_watches is None
                or conf_tyes is None
                or wuid not in conf_watches
                or str(description.key + "s") not in conf_tyes
            ):
                continue

            if description.key == SWITCH_ALARM:
                for alarm in await coordinator.controller.getWatchAlarm(wuid):
                    entities.append(XploraAlarmSwitch(config_entry, alarm, coordinator, ward, wuid, description))
            if description.key == SWITCH_SILENT:
                for silent in await coordinator.controller.getSilentTime(wuid):
                    entities.append(XploraSilentSwitch(config_entry, silent, coordinator, ward, wuid, description))

    async_add_entities(entities, True)


class XploraAlarmSwitch(XploraBaseEntity, SwitchEntity):
    """Create a Xplora alarm switch."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        alarm: dict[str, Any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        wuid: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize alarm switch."""
        super().__init__(config_entry, description, coordinator, wuid)
        if self.watch_uid not in self.coordinator.data:
            return

        self._alarm = alarm

        self._attr_name: str = (
            f"{ward.get(CONF_NAME)} {ATTR_WATCH} {description.key} {alarm['start']} ({coordinator.username})".replace(
                "_", " "
            ).title()
        )

        self._attr_unique_id = (
            f"{ward.get(CONF_NAME)}_{ATTR_WATCH}_{description.key}_{alarm['vendorId']}_{wuid}_{coordinator.user_id}".replace(
                " ", "_"
            )
            .replace("-", "_")
            .lower()
        )

        self._attr_is_on = self._states(alarm["status"])
        self._alarms: list[dict[str, Any]] = []
        _LOGGER.debug(
            "Updating switch: %s | Typ: %s | Watch_ID ...%s | state: %s | %s",
            self._attr_name,
            description.key,
            self.watch_uid[25:],
            self._attr_is_on,
            alarm["status"],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.coordinator.data[self.watch_uid] = self.coordinator.data[self.watch_uid]
        for alarm in self.coordinator.data[self.watch_uid].get("alarm", []):
            if alarm[ATTR_ID] == self._alarm[ATTR_ID]:
                self._attr_is_on = self._states(alarm["status"])
                self.async_write_ha_state()
        super()._handle_coordinator_update()

    async def _set_turn_on_off(self, status: bool) -> None:
        controller: PyXploraApi = self.hass.data[DOMAIN][self.entity_id].controller  # self.coordinator.controller
        if status:
            alarms = await controller.setEnableAlarmTime(alarm_id=self._alarm[ATTR_ID])
        else:
            alarms = await controller.setDisableAlarmTime(alarm_id=self._alarm[ATTR_ID])
        if alarms:
            self._attr_is_on = status

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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        data = super().extra_state_attributes or {}
        language = self._options.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        week_repeat = self._alarm["weekRepeat"]
        week_days = []
        for i, _ in enumerate(week_repeat):
            if week_repeat[i] == "1":
                week_days.append(DAYS.get(language, DEFAULT_LANGUAGE)[i])
        return dict(
            data,
            **{
                ATTR_SERVICE_USER: self.coordinator.controller.getUserName(),
                STR_DAYS.get(language, DEFAULT_LANGUAGE): ", ".join(week_days),
            },
        )


class XploraSilentSwitch(XploraBaseEntity, SwitchEntity):
    """Create a Xplora silent switch."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        silent: dict[str, Any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        wuid: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize silent switch."""
        super().__init__(config_entry, description, coordinator, wuid)
        if self.watch_uid not in self.coordinator.data:
            return
        self.coordinator.data[self.watch_uid]: dict[str, Any] = self.coordinator.data[self.watch_uid]

        self._silent = silent

        self._attr_name: str = f"{ward.get(CONF_NAME)} {ATTR_WATCH} {description.key} {silent['start']}-{silent['end']} ({coordinator.username})".replace(  # noqa: E501
            "_", " "
        ).title()

        self._attr_unique_id = (
            f"{ward.get(CONF_NAME)}_{ATTR_WATCH}_{description.key}_{silent['vendorId']}_{wuid}_{coordinator.user_id}".replace(
                " ", "_"
            )
            .replace("-", "_")
            .lower()
        )

        self._attr_is_on = self._states(silent["status"])
        self._silents: list[dict[str, Any]] = []
        _LOGGER.debug(
            "Updating switch: %s | Typ: %s | Watch_ID ...%s | state: %s | %s",
            self._attr_name,
            description.key,
            self.watch_uid[25:],
            self._attr_is_on,
            silent["status"],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.coordinator.data[self.watch_uid] = self.coordinator.data[self.watch_uid]
        for silent in self.coordinator.data[self.watch_uid].get("silent", []):
            if silent[ATTR_ID] == self._silent[ATTR_ID]:
                self._attr_is_on = self._states(silent["status"])
                self.async_write_ha_state()
        super()._handle_coordinator_update()

    async def _set_turn_on_off(self, status: bool) -> None:
        """Set the turn on / off state."""
        controller: PyXploraApi = self.coordinator.controller
        if status:
            silents = await controller.setEnableSilentTime(silent_id=self._silent[ATTR_ID])
        else:
            silents = await controller.setDisableSilentTime(silent_id=self._silent[ATTR_ID])
        if silents:
            self._attr_is_on = status

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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        data = super().extra_state_attributes or {}
        language = self._options.get(CONF_LANGUAGE, self._data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        week_repeat = self._silent["weekRepeat"]
        week_days = []
        for i, _ in enumerate(week_repeat):
            if week_repeat[i] == "1":
                week_days.append(DAYS.get(language, DEFAULT_LANGUAGE)[i])
        return dict(
            data,
            **{
                ATTR_SERVICE_USER: self.coordinator.controller.getUserName(),
                STR_DAYS.get(language, DEFAULT_LANGUAGE): ", ".join(week_days),
            },
        )
