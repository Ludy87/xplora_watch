"""Coordinator for Xplora® Watch Version 2"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from pyxplora_api import pyxplora_api_async as PXA
from pyxplora_api.model import ChatsNew

from homeassistant.components.device_tracker.const import ATTR_BATTERY, ATTR_LOCATION_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
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
    CONF_REMOVE_MESSAGE,
    CONF_TIMEZONE,
    CONF_USERLANG,
    CONF_WATCHES,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAPS,
    SENSOR_MESSAGE,
    SENSOR_XCOIN,
    URL_OPENSTREETMAP,
)
from .geocoder import OpenCageGeocodeUA

_LOGGER = logging.getLogger(__name__)


class XploraDataUpdateCoordinator(DataUpdateCoordinator):
    location_name: str = None
    licence: str = None
    controller: PXA.PyXploraApi = None
    lat: float | None = None
    lng: float | None = None
    poi: str | None = None
    location_accuracy: int = -1
    locateType: str = PXA.LocationType.UNKNOWN.value
    lastTrackTime: str | None = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize Xplora® data updater."""
        self._entry = entry
        self._opencage_apikey = entry.options.get(CONF_OPENCAGE_APIKEY, "")
        self._maps = entry.options.get(CONF_MAPS, MAPS[0])
        self._xcoin = 0
        name = f"{DOMAIN}-"
        if CONF_PHONENUMBER in entry.data:
            name += entry.data[CONF_PHONENUMBER][5:]
        elif CONF_EMAIL in entry.data:
            name += entry.data[CONF_EMAIL]
        super().__init__(
            hass,
            _LOGGER,
            name=f'{DOMAIN}-{entry.data[CONF_PHONENUMBER][5:] if CONF_EMAIL not in entry.data else ""}',
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )

    async def set_controller(self, session) -> None:
        data = self._entry.data
        options = self._entry.options
        self.controller = PXA.PyXploraApi(
            countrycode=data.get(CONF_COUNTRY_CODE),
            phoneNumber=data.get(CONF_PHONENUMBER),
            password=data[CONF_PASSWORD],
            userLang=data[CONF_USERLANG],
            timeZone=data[CONF_TIMEZONE],
            wuid=options.get(CONF_WATCHES),
            email=data.get(CONF_EMAIL),
            session=session,
        )

    async def init(self, session=None) -> None:
        await self.set_controller(session)
        await self.controller.init(self.controller._gql_handler.getApiKey(), sec=self.controller._gql_handler.getSecret())

    async def _async_update_data(self, targets: list[str] = None):
        """Fetch data from Xplora."""
        # Initialize the watch entry data
        await self.init(aiohttp_client.async_create_clientsession(self.hass))
        _LOGGER.debug("pyxplora_api lib version: %s", self.controller.version())

        # Get the list of watch UUIDs
        if targets:
            wuids = await self.controller.setDevices(targets)
        else:
            wuids = self._entry.options.get(CONF_WATCHES, await self.controller.setDevices())

        # Get the message limit and remove message option
        message_limit = self._entry.options.get(CONF_MESSAGE, 10)
        remove_message = self._entry.options.get(CONF_REMOVE_MESSAGE, False)

        # Loop through the list of watches and fetch data
        for wuid in wuids:
            _LOGGER.debug("Fetch data from Xplora: %s", wuid[25:])
            device = self.controller.getDevice(wuid=wuid)
            res_chats = await self.controller.getWatchChatsRaw(wuid, limit=message_limit, show_del_msg=remove_message)
            chats = ChatsNew.from_dict(res_chats).to_dict()
            watch_location = await self.controller.loadWatchLocation(wuid)

            # Update the watch data
            self.unreadMsg = await self.controller.getWatchUnReadChatMsgCount(wuid)
            self.battery = watch_location.get("watch_battery", -1)
            self.isCharging = watch_location.get("watch_charging", False)
            self.get_location(device, watch_location)

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
            self._xcoin = device.get("getWatchUserXcoins", 0)
            await self.get_map()
            data = self.get_data(wuid, chats)
        return data

    def get_location(self, device, watch_location):
        if watch_location.get(ATTR_TRACKER_LAT, None):
            self.lat = float(watch_location.get(ATTR_TRACKER_LAT, 0.0))
        if watch_location.get(ATTR_TRACKER_LNG, None):
            self.lng = float(watch_location.get(ATTR_TRACKER_LNG, 0.0))
        self.poi = watch_location.get(ATTR_TRACKER_POI, "")
        self.location_accuracy = watch_location.get(ATTR_TRACKER_RAD, -1)
        self.locateType = watch_location.get("locateType", PXA.LocationType.UNKNOWN.value)
        self.lastTrackTime = device.get("lastTrackTime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    async def get_map(self):
        if self._maps == MAPS[1] and self.lat and self.lng:
            async with OpenCageGeocodeUA(self._opencage_apikey) as geocoder:
                results: list[Any] = await geocoder.reverse_geocode_async(
                    self.lat, self.lng, no_annotations=1, pretty=1, no_record=1, no_dedupe=1, limit=1, abbrv=1
                )
                self.location_name = results[0]["formatted"]
                self.licence = (await geocoder.licenses_async(self.lat, self.lng))[0]["url"]
                _LOGGER.debug("load address from opencagedata.com")
        elif self._maps == MAPS[0] and self.lat and self.lng:
            language = self._entry.options.get(CONF_LANGUAGE, self._entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
            timeout = aiohttp.ClientTimeout(total=2)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # codiga-disable
                async with session.get(URL_OPENSTREETMAP.format(self.lat, self.lng, language)) as response:
                    res: dict[str, Any] = await response.json()
                    self.licence = res.get(ATTR_TRACKER_LICENCE, None)
                    address: dict[str, str] = res.get(ATTR_TRACKER_ADDR, {})
                    if address:
                        self.location_name = res.get("display_name", "")
                        _LOGGER.debug("load address from openstreetmap.org")

    def get_data(self, wuid, chats):
        return {
            wuid: {
                "unreadMsg": self.unreadMsg,
                ATTR_BATTERY: self.battery if self.battery != -1 else None,
                "isCharging": self.isCharging if self.battery != -1 else None,
                "isOnline": self.isOnline,
                "isSafezone": self.isSafezone,
                "alarm": self.alarm,
                "silent": self.silent,
                "step_day": self._step_day,
                SENSOR_XCOIN: self._xcoin,
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
                ATTR_TRACKER_LICENCE: self.licence,
                SENSOR_MESSAGE: chats,
            }
        }
