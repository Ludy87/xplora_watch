"""Coordinator for Xplora® Watch Version 2"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from pyxplora_api import pyxplora_api_async as PXA

from homeassistant.components.device_tracker.const import ATTR_BATTERY, ATTR_LOCATION_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_IMEI,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LICENCE,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_RAD,
    CONF_COUNTRY_CODE,
    CONF_LANGUAGE,
    CONF_MAPS,
    CONF_MESSAGE,
    CONF_OPENCAGE_APIKEY,
    CONF_PHONENUMBER,
    CONF_TIMEZONE,
    CONF_USERLANG,
    CONF_WATCHES,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAPS,
    URL_OPENSTREETMAP,
)
from .geocoder import OpenCageGeocodeUA

_LOGGER = logging.getLogger(__name__)


class XploraDataUpdateCoordinator(DataUpdateCoordinator):
    location_name: str = None
    controller: PXA.PyXploraApi

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize Xplora® data updater."""
        self._entry = entry
        self.opencage_apikey = entry.options.get(CONF_OPENCAGE_APIKEY, "")
        self.maps = entry.options.get(CONF_MAPS, MAPS[0])
        super().__init__(
            hass,
            _LOGGER,
            name=f'{DOMAIN}-{entry.data[CONF_PHONENUMBER][5:] if CONF_EMAIL not in entry.data else ""}',
            update_method=self._async_update_watch_data,
            update_interval=timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )

    async def init(self) -> PXA.PyXploraApi:
        self.controller: PXA.PyXploraApi = PXA.PyXploraApi(
            countrycode=self._entry.data.get(CONF_COUNTRY_CODE, None),
            phoneNumber=self._entry.data.get(CONF_PHONENUMBER, None),
            password=self._entry.data[CONF_PASSWORD],
            userLang=self._entry.data[CONF_USERLANG],
            timeZone=self._entry.data[CONF_TIMEZONE],
            wuid=self._entry.options.get(CONF_WATCHES, None),
            email=self._entry.data.get(CONF_EMAIL, None),
        )
        await self.controller.init(forceLogin=True)
        return self.controller

    async def _async_update_watch_data(self, targets: list[str] | None = None) -> dict[str, Any]:
        """Fetch data from Xplora®."""
        await self.init()
        _LOGGER.debug("pyxplora_api Lib version: %s", self.controller.version())
        self.watch_entry: dict[str, Any] = {}
        if self.data:
            self.watch_entry.update(self.data)
        if targets:
            wuids = await self.controller.setDevices(targets)
        else:
            wuids = self._entry.options.get(CONF_WATCHES, await self.controller.setDevices())
        for wuid in wuids:
            _LOGGER.debug("Fetch data from Xplora®: %s", wuid[25:])
            device: dict[str, Any] = self.controller.getDevice(wuid=wuid)

            chats: dict[str, Any] = (
                await self.controller.getWatchChatsRaw(wuid, limit=self._entry.options.get(CONF_MESSAGE, 10))
            ).get("chatsNew", {"list: []"})

            watchLocate: dict[str, Any] = device.get("loadWatchLocation", {})
            self.unreadMsg = await self.controller.getWatchUnReadChatMsgCount(wuid)
            self.battery = watchLocate.get("watch_battery", -1)
            self.isCharging = watchLocate.get("watch_charging", False)
            self.lat = float(watchLocate.get(ATTR_TRACKER_LAT, 0.0))
            self.lng = float(watchLocate.get(ATTR_TRACKER_LNG, 0.0))
            self.poi = watchLocate.get(ATTR_TRACKER_POI, "")
            self.location_accuracy = watchLocate.get(ATTR_TRACKER_RAD, -1)
            self.locateType = watchLocate.get("locateType", PXA.LocationType.UNKNOWN.value)
            self.lastTrackTime = device.get("lastTrackTime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            self.isSafezone = False if device.get("isInSafeZone", False) else True

            self.isOnline = (
                True
                if device.get("getWatchOnlineStatus", PXA.WatchOnlineStatus.UNKNOWN.value)
                == PXA.WatchOnlineStatus.ONLINE.value
                else False
            )

            self.alarm = device.get("getWatchAlarm", [])
            self.silent = device.get("getSilentTime", [])

            sw_version: dict[str, Any] = device.get("getWatches", {})
            self.imei = sw_version.get(ATTR_TRACKER_IMEI, wuid)
            self.watch_id = wuid
            self.os_version = sw_version.get("osVersion", "n/a")
            self.model = sw_version.get("model", "GPS-Watch")
            self.entity_picture = device.get("getWatchUserIcons", "")

            self._step_day = device.get("getWatchUserSteps", {}).get("day")
            self._xcoin = device.get("getWatchUserXcoins", Any)
            licence = None
            if self.maps == MAPS[1]:
                async with OpenCageGeocodeUA(self.opencage_apikey) as geocoder:
                    results: list[Any] = await geocoder.reverse_geocode_async(
                        self.lat, self.lng, no_annotations=1, pretty=1, no_record=1, no_dedupe=1, limit=1, abbrv=1
                    )
                    self.location_name = results[0]["formatted"]
                _LOGGER.debug("load address from opencagedata.com")
            else:
                language = self._entry.options.get(CONF_LANGUAGE, self._entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
                timeout = aiohttp.ClientTimeout(total=2)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # codiga-disable
                    async with session.get(URL_OPENSTREETMAP.format(self.lat, self.lng, language)) as response:
                        await session.close()
                        res: dict[str, Any] = await response.json()
                        licence = res.get(ATTR_TRACKER_LICENCE, None)
                        address: dict[str, str] = res.get(ATTR_TRACKER_ADDR, {})
                        if address:
                            self.location_name = res.get("display_name", "")
                            _LOGGER.debug("load address from openstreetmap.org")
            self.watch_entry.update(
                {
                    wuid: {
                        "unreadMsg": self.unreadMsg,
                        ATTR_BATTERY: self.battery if self.battery != -1 else None,
                        "isCharging": self.isCharging if self.battery != -1 else None,
                        "isOnline": self.isOnline,
                        "isSafezone": self.isSafezone,
                        "alarm": self.alarm,
                        "silent": self.silent,
                        "step_day": self._step_day,
                        "xcoin": self._xcoin,
                        ATTR_TRACKER_LAT: self.lat if self.isOnline else None,
                        ATTR_TRACKER_LNG: self.lng if self.isOnline else None,
                        ATTR_TRACKER_POI: self.poi if self.poi else None,
                        ATTR_LOCATION_NAME: self.location_name,
                        ATTR_TRACKER_IMEI: self.imei,
                        "location_accuracy": self.location_accuracy,
                        "entity_picture": self.entity_picture,
                        "os_version": self.os_version,
                        "model": self.model,
                        "watch_id": self.watch_id,
                        "locateType": self.locateType,
                        "lastTrackTime": self.lastTrackTime,
                        ATTR_TRACKER_LICENCE: licence,
                        "message": chats,
                    }
                }
            )
        if self.data:
            self.data.update(self.watch_entry)
        else:
            self.data = self.watch_entry
        return self.data

    # @callback
    # def async_set_updated_data(self, data: dict) -> None:
    #     """Manually update data, notify listeners and reset refresh interval, and remember."""
    #     super().async_set_updated_data(data)
