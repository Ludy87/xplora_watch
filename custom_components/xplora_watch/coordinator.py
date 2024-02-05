"""Coordinator for Xplora® Watch Version 2."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from pyxplora_api.const import DEFAULT_TIMEOUT
from pyxplora_api.model import ChatsNew
from pyxplora_api.pyxplora_api_async import PyXploraApi
from pyxplora_api.status import LocationType, WatchOnlineStatus

from homeassistant.components.device_tracker.const import (
    ATTR_BATTERY,
    ATTR_LOCATION_NAME,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_COUNTRY_CODE,
    CONF_EMAIL,
    CONF_LANGUAGE,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    API_KEY_MAPBOX,
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_IMEI,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LICENCE,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_RAD,
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
    URL_MAPBOX,
    URL_OPENSTREETMAP,
)
from .geocoder import OpenCageGeocodeUA

_LOGGER = logging.getLogger(__name__)


class XploraDataUpdateCoordinator(DataUpdateCoordinator):
    """Create XploraDataUpdateCoordinator that manages data updates."""

    location_name: str | None = None
    licence: str | None = None
    controller: PyXploraApi = None
    lat: float | None = None
    lng: float | None = None
    poi: str | None = None
    location_accuracy: int = -1
    locate_type: str = LocationType.UNKNOWN.value
    last_track_time: str | None = None
    unread_msg: int = -1
    battery: int = -1
    is_charging: bool = False
    is_safezone: bool = False
    is_online: bool = False
    device: dict[str, Any] = {}
    username: str
    user_id: str
    is_admin: dict[str, bool] = {}
    alarm: list = []
    silent: list = []
    imei: str = ""
    watch_id: str | None = None
    os_version: str = "n/a"
    model: str = "GPS-Watch"
    entity_picture: str = ""
    _step_day: dict
    _xcoin: int

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize Xplora® data updater."""
        self._entry: ConfigEntry = entry
        self._opencage_apikey = entry.options.get(CONF_OPENCAGE_APIKEY, "")
        self._maps = entry.options.get(CONF_MAPS, MAPS[0])
        name = f"{DOMAIN}-"
        if CONF_PHONENUMBER in entry.data:
            name += entry.data[CONF_PHONENUMBER][5:]
        elif CONF_EMAIL in entry.data:
            name += entry.data[CONF_EMAIL]

        _scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        if _scan_interval == 0 or _scan_interval is None:
            _update_interval = None
            _LOGGER.debug("Update interval disable")
        else:
            _update_interval = timedelta(seconds=_scan_interval)
        super().__init__(
            hass,
            _LOGGER,
            name=f'{DOMAIN}-{entry.data[CONF_PHONENUMBER][5:] if CONF_EMAIL not in entry.data else ""}',
            update_method=self.async_update_xplora_data,
            update_interval=_update_interval,
        )

    async def set_controller(self, session) -> None:
        """Set the controller to use."""
        data = self._entry.data
        options = self._entry.options
        self.controller: PyXploraApi = PyXploraApi(
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
        """Init Coordinator."""
        await self.set_controller(session)
        await self.controller.init(
            forceLogin=True
        )  # key=self.controller._gql_handler.getApiKey(), sec=self.controller._gql_handler.getSecret()

        self.username = self.controller.getUserName()
        self.user_id = self.controller.getUserID()
        new_name = self.user_id + self._entry.entry_id
        for watch in self.controller.getWatchUserIDs():
            _is_admin = await self.controller.isAdmin(watch)
            if new_name in self.is_admin:
                continue
            self.is_admin.update({new_name: _is_admin})

    async def async_update_xplora_data(self, targets: list[str] | None = None, new_data: dict | None = None):
        """Fetch data from Xplora."""
        # Initialize the watch entry data
        if new_data:
            _LOGGER.debug("new data from Message Service")
            if self.data:
                self.data.update(new_data)
            else:
                self.data = new_data
            self.async_set_updated_data(self.data)
            return
        watch_entry = {}
        if self.data:
            watch_entry.update(self.data)

        await self.init(aiohttp_client.async_get_clientsession(self.hass))

        # Get the list of watch UUIDs
        if targets:
            wuids = await self.controller.setDevices(targets)
        else:
            wuids = self._entry.options.get(CONF_WATCHES, await self.controller.setDevices())

        # Get the message limit and remove message option
        message_limit = self._entry.options.get(CONF_MESSAGE, 10)
        message_limit = message_limit if isinstance(message_limit, int) else 10
        remove_message = self._entry.options.get(CONF_REMOVE_MESSAGE, False)

        # Loop through the list of watches and fetch data
        watch_entry.update(await self.data_loop(wuids, message_limit, remove_message))
        if not self.data:
            self.data = watch_entry
        else:
            self.data.update(watch_entry)
        self.async_set_updated_data(self.data)
        return self.data

    async def data_loop(self, wuids: list[str], message_limit, remove_message):
        """Fetch and parse Xplora data."""
        data = {}
        for wuid in wuids:
            _LOGGER.debug("Fetch data from Xplora: %s", wuid[25:])
            self.device = self.controller.getDevice(wuid=wuid)
            res_chats = await self.controller.getWatchChatsRaw(wuid, limit=message_limit, show_del_msg=remove_message)
            chats = ChatsNew.from_dict(res_chats).to_dict()
            watch_location = await self.controller.loadWatchLocation(wuid)

            # Update the watch data
            self.unread_msg = await self.controller.getWatchUnReadChatMsgCount(wuid)
            self.battery = self.device.get("watch_battery", -1)
            self.is_charging = self.device.get("watch_charging", False)
            self.get_location(watch_location)

            self.is_safezone = False if self.device.get("isInSafeZone", False) else True

            self.is_online = (
                True
                if self.device.get("getWatchOnlineStatus", WatchOnlineStatus.UNKNOWN.value) == WatchOnlineStatus.ONLINE.value
                else False
            )

            await self.get_watch_functions(wuid, self.device)
            await self.get_map()
            data.update(self.get_data(wuid, chats))
        return data

    async def get_watch_functions(self, wuid: str, device: dict[str, Any]):
        """Get functions that need to be called when a watch is created."""
        await self.init(aiohttp_client.async_get_clientsession(self.hass))
        self.alarm = await self.controller.getWatchAlarm(wuid=wuid)  # device.get("getWatchAlarm", [])
        self.silent = device.get("getSilentTime", [])

        sw_version: dict[str, Any] = device.get("getWatches", {})
        self.imei = sw_version.get(ATTR_TRACKER_IMEI, wuid)
        self.watch_id = wuid
        self.os_version = sw_version.get("osVersion", "n/a")
        self.model = sw_version.get("model", "GPS-Watch")
        self.entity_picture = device.get("getWatchUserIcons", "")

        self._step_day = device.get("getWatchUserSteps", {}).get("day")
        self._xcoin = device.get("getWatchUserXCoins", 0)

    def get_location(self, watch_location):
        """Get location information from device."""
        self.lat = float(self.device.get(ATTR_TRACKER_LAT, 0.0)) if self.device.get(ATTR_TRACKER_LAT, None) else None
        self.lng = float(self.device.get(ATTR_TRACKER_LNG, 0.0)) if self.device.get(ATTR_TRACKER_LNG, None) else None
        self.poi = watch_location.get(ATTR_TRACKER_POI, None)
        self.location_accuracy = self.device.get(ATTR_TRACKER_RAD, -1)
        self.locate_type = watch_location.get("locateType", LocationType.UNKNOWN.value)
        self.last_track_time = self.device.get("lastTrackTime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    async def get_map(self):
        """Get map."""
        if self._maps == MAPS[1] and self.lat and self.lng:
            await self.opencagedata()
        elif self._maps == MAPS[0] and self.lat and self.lng:
            await self.openstreetmap()

    async def mapbox(self):
        """Get mapbox information for the location."""
        language = self._entry.options.get(CONF_LANGUAGE, self._entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        async with aiohttp.ClientSession() as session:
            url = URL_MAPBOX.format(self.lng, self.lat, API_KEY_MAPBOX, language)
            async with session.get(url) as response:
                data = await response.json()
                if data["features"]:
                    self.location_name = data["features"][0]["place_name"]
                    self.licence = data["attribution"]
                self.licence = data["attribution"]

    async def opencagedata(self):
        """Get opencagedata.com information for the location.."""
        try:
            async with OpenCageGeocodeUA(self._opencage_apikey) as geocoder:
                results: list[Any] = await geocoder.reverse_geocode_async(
                    self.lat, self.lng, no_annotations=1, pretty=1, no_record=1, no_dedupe=1, limit=1, abbrv=1
                )
                self.location_name = results[0]["formatted"]
                self.licence = (await geocoder.licenses_async(self.lat, self.lng))[0]["url"]
                _LOGGER.debug("load address from opencagedata.com")
        except aiohttp.ContentTypeError:
            _LOGGER.debug("error about open.com using mapbox.com")
            await self.mapbox()

    async def openstreetmap(self):
        """Get OpenStreetMap.org information for the location.."""
        try:
            language = self._entry.options.get(CONF_LANGUAGE, self._entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(DEFAULT_TIMEOUT)) as session, session.get(
                URL_OPENSTREETMAP.format(self.lat, self.lng, language)
            ) as response:
                res: dict[str, Any] = await response.json()
                self.licence = res.get(ATTR_TRACKER_LICENCE, None)
                address: dict[str, str] = res.get(ATTR_TRACKER_ADDR, {})
                if address:
                    self.location_name = res.get("display_name", "")
                    _LOGGER.debug("load address from openstreetmap.org")
        except aiohttp.ContentTypeError:
            _LOGGER.debug("error about openstreetmap.org using mapbox.com")
            await self.mapbox()

    def get_data(self, wuid, chats):
        """Get data for a given wuid."""
        return {
            wuid: {
                "unreadMsg": self.unread_msg,
                ATTR_BATTERY: self.battery if self.battery != -1 else None,
                "isCharging": self.is_charging if self.battery != -1 else None,
                "isOnline": self.is_online,
                "isSafezone": self.is_safezone,
                "alarm": self.alarm,
                "silent": self.silent,
                "step_day": self._step_day,
                SENSOR_XCOIN: self._xcoin,
                ATTR_TRACKER_LAT: self.lat if self.is_online else None,
                ATTR_TRACKER_LNG: self.lng if self.is_online else None,
                ATTR_TRACKER_POI: self.poi if self.poi else None,
                ATTR_LOCATION_NAME: self.location_name,
                ATTR_TRACKER_IMEI: self.imei,
                "location_accuracy": self.location_accuracy,
                "entity_picture": self.entity_picture,
                "os_version": self.os_version,
                "model": self.model,
                "watch_id": self.watch_id,
                "locateType": self.locate_type,
                "lastTrackTime": self.last_track_time,
                ATTR_TRACKER_LICENCE: self.licence,
                SENSOR_MESSAGE: chats,
            }
        }

    async def message_data(self, wuid, message_limit, remove_message) -> dict | ChatsNew:
        """Fetch message chats from Xplora."""
        watch_entry = {}
        if self.data:
            watch_entry.update(self.data)
        _LOGGER.debug("Fetch message data from Xplora: %s", wuid[25:])
        res_chats = await self.controller.getWatchChatsRaw(wuid, limit=message_limit, show_del_msg=remove_message)
        chats = ChatsNew.from_dict(res_chats).to_dict()
        watch_entry.update({wuid: {SENSOR_MESSAGE: chats}})
        self.data = watch_entry
        return res_chats
