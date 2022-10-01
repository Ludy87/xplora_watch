"""Coordinator for Xplora® Watch Version 2"""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from pyxplora_api import pyxplora_api_async as PXA

from .const import (
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_IMEI,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LICENCE,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_RAD,
    CONF_COUNTRY_CODE,
    CONF_MAPS,
    CONF_OPENCAGE_APIKEY,
    CONF_PHONENUMBER,
    CONF_TIMEZONE,
    CONF_USERLANG,
    CONF_WATCHES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAPS,
)
from .geocoder import OpenCageGeocodeUA

import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class XploraDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize Xplora® data updater."""
        self.controller = PXA.PyXploraApi(
            countrycode=entry.data[CONF_COUNTRY_CODE],
            phoneNumber=entry.data[CONF_PHONENUMBER],
            password=entry.data[CONF_PASSWORD],
            userLang=entry.data[CONF_USERLANG],
            timeZone=entry.data[CONF_TIMEZONE],
            wuid=entry.options.get(CONF_WATCHES, None),
        )
        self._entry = entry
        self.opencage_apikey = entry.options.get(CONF_OPENCAGE_APIKEY, "")
        self.maps = entry.options.get(CONF_MAPS, MAPS[0])
        super().__init__(
            hass,
            _LOGGER,
            name="{}-{}".format(DOMAIN, entry.data[CONF_PHONENUMBER][5:]),
            update_method=self._async_update_watch_data,
            update_interval=timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )

    async def init(self) -> None:
        await self.controller.init(True)

    async def _async_update_watch_data(self) -> dict[str, any]:
        """Fetch data from Xplora®."""
        await self.init()
        self.watch_entry: dict[str, any] = {}
        if self.data:
            self.watch_entry.update(self.data)
        ids = self._entry.options.get(CONF_WATCHES, await self.controller.setDevices())
        for wuid in ids:
            _LOGGER.debug(f"Fetch data from Xplora®: {wuid[25:]}")
            device: dict[str, any] = self.controller.getDevice(wuid=wuid)

            watchLocate: dict[str, any] = device.get("loadWatchLocation", {})

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

            sw_version: dict[str, any] = device.get("getWatches", {})
            self.imei = sw_version.get(ATTR_TRACKER_IMEI, wuid)
            self.watch_id = wuid
            self.os_version = sw_version.get("osVersion", "n/a")
            self.model = sw_version.get("model", "GPS-Watch")
            self.entity_picture = device.get("getWatchUserIcons", "")

            self._step_day = device.get("getWatchUserSteps", {}).get("day")
            self._xcoin = device.get("getWatchUserXcoins", any)
            timeout = aiohttp.ClientTimeout(total=2)
            licence = None
            if self.maps == MAPS[1]:
                async with OpenCageGeocodeUA(self.opencage_apikey) as geocoder:
                    results: list[any] = await geocoder.reverse_geocode_async(
                        self.lat, self.lng, no_annotations=1, pretty=1, no_record=1, no_dedupe=1, limit=1, abbrv=1
                    )
                    self.location_name = "{}".format(results[0]["formatted"])
                _LOGGER.debug("load address from opencagedata.com")
            else:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        "https://nominatim.openstreetmap.org/reverse?lat={}&lon={}&format=jsonv2".format(self.lat, self.lng)
                    ) as response:
                        await session.close()
                        res: dict[str, any] = await response.json()
                        licence = res.get(ATTR_TRACKER_LICENCE, None)
                        address: dict[str, str] = res.get(ATTR_TRACKER_ADDR, [])
                        if address:
                            self.location_name = "{}".format(res.get("display_name", ""))
                            _LOGGER.debug("load address from openstreetmap.org")
            self.watch_entry.update(
                {
                    wuid: {
                        "battery": self.battery if self.battery != -1 else None,
                        "isCharging": self.isCharging if self.battery != -1 else None,
                        "isOnline": self.isOnline,
                        "isSafezone": self.isSafezone,
                        "alarm": self.alarm,
                        "silent": self.silent,
                        "step_day": self._step_day,
                        "xcoin": self._xcoin,
                        ATTR_TRACKER_LAT: self.lat if self.isOnline else None,
                        ATTR_TRACKER_LNG: self.lng if self.isOnline else None,
                        ATTR_TRACKER_POI: self.poi,
                        "location_name": self.location_name,
                        ATTR_TRACKER_IMEI: self.imei,
                        "location_accuracy": self.location_accuracy,
                        "entity_picture": self.entity_picture,
                        "os_version": self.os_version,
                        "model": self.model,
                        "watch_id": self.watch_id,
                        "locateType": self.locateType,
                        "lastTrackTime": self.lastTrackTime,
                        ATTR_TRACKER_LICENCE: licence,
                    }
                }
            )
        if self.data:
            self.data.update(self.watch_entry)
        else:
            self.data = self.watch_entry
        return self.data
