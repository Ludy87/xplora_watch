"""Support for Xplora® Watch tracking."""
from __future__ import annotations

import logging

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from .geocoder import OpenCageGeocodeUA

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from geopy import distance

from .const import (
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_CITY,
    ATTR_TRACKER_COUNTRY,
    ATTR_TRACKER_COUNTRY_ABBR,
    ATTR_TRACKER_DISTOHOME,
    ATTR_TRACKER_ISINSAFEZONE,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_PROVINCE,
    ATTR_TRACKER_RAD,
    ATTR_TRACKER_SAFEZONEADRESS,
    ATTR_TRACKER_SAFEZONEGROUPNAME,
    ATTR_TRACKER_SAFEZONELABEL,
    ATTR_TRACKER_SAFEZONENAME,
    CONF_OPENCAGE_APIKEY,
    CONF_SAFEZONES,
    CONF_TRACKER_SCAN_INTERVAL,
    CONF_TYPES,
    CONF_WATCHUSER_ID,
    DATA_XPLORA,
    DEVICE_TRACKER_WATCH,
    XPLORA_CONTROLLER,
)
from .helper import XploraDevice

from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    async_see: Callable[..., Awaitable[None]],
    discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Validate the configuration and return a Xplora® scanner."""
    if discovery_info is None:
        return False

    if DEVICE_TRACKER_WATCH not in hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]:
        return False
    _LOGGER.debug("set Tracker")

    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    opencage: str = hass.data[CONF_OPENCAGE_APIKEY][discovery_info[XPLORA_CONTROLLER]]
    scan_interval: timedelta = hass.data[CONF_TRACKER_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time: float = datetime.timestamp(datetime.now())
    watch_ids: list = hass.data[CONF_WATCHUSER_ID][discovery_info[XPLORA_CONTROLLER]]

    if hass.data[CONF_SAFEZONES][discovery_info[XPLORA_CONTROLLER]] == "show":
        _LOGGER.debug("show safezone")
        for watch_id in watch_ids:
            i = 1
            for safeZone in await controller.getSafeZones(watch_id):
                if safeZone:
                    lat = float(safeZone.get("lat"))
                    lng = float(safeZone.get("lng"))
                    rad = safeZone.get("rad")
                    attr = {}
                    if safeZone.get("name", None):
                        attr[ATTR_TRACKER_SAFEZONENAME] = safeZone.get("name")
                    if safeZone.get("address", None):
                        attr[ATTR_TRACKER_SAFEZONEADRESS] = safeZone.get("address")
                    if safeZone.get("groupName", None):
                        attr[ATTR_TRACKER_SAFEZONEGROUPNAME] = safeZone.get("groupName")
                    await async_see(
                        source_type=SOURCE_TYPE_GPS,
                        dev_id=slugify("Safezone " + str(i) + " " + watch_id),
                        gps=(lat, lng),
                        gps_accuracy=rad,
                        host_name=safeZone.get("name") + " " + watch_id,
                        attributes=attr,
                        icon="mdi:crosshairs-gps",
                    )
                    i += 1

    _LOGGER.debug("set WatchScanner")
    scanner = WatchScanner(
        hass,
        async_see,
        controller,
        scan_interval,
        start_time,
        watch_ids,
        opencage,
    )
    return await scanner.async_init()


class WatchScanner(XploraDevice):
    def __init__(
        self,
        hass,
        async_see,
        controller,
        scan_interval,
        start_time,
        watch_ids,
        opencage,
    ) -> None:
        """Initialize."""
        super().__init__(scan_interval, start_time)
        self.connected = False
        self._controller: PXA.PyXploraApi = controller
        self._watch_ids = watch_ids
        self._async_see = async_see
        self._hass: HomeAssistant = hass
        self._watch_location = None
        self._opencage = opencage

    async def async_init(self) -> bool:
        """Further initialize connection to Xplora® API."""
        _LOGGER.debug("set async_init")
        await self._controller.init()
        for watch_id in self._watch_ids:
            username = self._controller.getWatchUserName(watch_id)
            if username is None:
                _LOGGER.error("Can not connect to Xplora® API")
                return False

        await self._async_update()
        async_track_time_interval(self._hass, self._async_update, self._scan_interval)
        return True

    async def _async_update(self, now=None) -> None:
        """Update info from Xplora® API."""
        xts_state = 'on'
        xts = self._hass.states.get('input_boolean.xplora_tracker_switch')
        if xts:
            xts_state = xts.state
        if (self._update_timer() and xts_state == 'on') or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            for watch_id in self._watch_ids:
                _LOGGER.debug(f"Updating device data {watch_id}")
                self._watch_location = await self._controller.getWatchLastLocation(watchID=watch_id, withAsk=True)
                self._hass.async_create_task(self.import_device_data(watch_id))

    def get_location_distance(self, watch_c):
        home_zone = self._hass.states.get('zone.home').attributes
        return int(distance.distance((home_zone[ATTR_TRACKER_LAT], home_zone[ATTR_TRACKER_LNG]), watch_c).m)

    async def import_device_data(self, watch_id) -> None:
        """Import device data from Xplora® API."""
        watch_location_info = self._watch_location
        attr = {}
        if watch_location_info.get("lat", None):
            attr[ATTR_TRACKER_LAT] = float(watch_location_info["lat"])
        if watch_location_info.get("lng", None):
            attr[ATTR_TRACKER_LNG] = float(watch_location_info["lng"])
        if watch_location_info.get("rad", None):
            attr[ATTR_TRACKER_RAD] = watch_location_info["rad"]
        if watch_location_info.get(ATTR_TRACKER_COUNTRY, None):
            attr[ATTR_TRACKER_COUNTRY] = watch_location_info[ATTR_TRACKER_COUNTRY]
        if watch_location_info.get(ATTR_TRACKER_COUNTRY_ABBR, None):
            attr[ATTR_TRACKER_COUNTRY_ABBR] = watch_location_info[ATTR_TRACKER_COUNTRY_ABBR]
        if watch_location_info.get(ATTR_TRACKER_PROVINCE, None):
            attr[ATTR_TRACKER_PROVINCE] = watch_location_info[ATTR_TRACKER_PROVINCE]
        if watch_location_info.get(ATTR_TRACKER_CITY, None):
            attr[ATTR_TRACKER_CITY] = watch_location_info[ATTR_TRACKER_CITY]
        if watch_location_info.get(ATTR_TRACKER_ADDR, None):
            if self._opencage == '':
                attr[ATTR_TRACKER_ADDR] = watch_location_info[ATTR_TRACKER_ADDR]
            else:
                _LOGGER.debug("load addr from OpenCageData")
                async with OpenCageGeocodeUA(self._opencage) as geocoder:
                    results: dict = await geocoder.reverse_geocode_async(
                        watch_location_info.get("lat"), watch_location_info.get("lng"),
                        no_annotations=1,
                        pretty=1,
                        no_record=1,
                        no_dedupe=1,
                        limit=1,
                        abbrv=1
                    )
                    attr[ATTR_TRACKER_ADDR] = results[0]['formatted']

        if watch_location_info.get(ATTR_TRACKER_POI, None):
            attr[ATTR_TRACKER_POI] = watch_location_info[ATTR_TRACKER_POI]
        if watch_location_info.get(ATTR_TRACKER_ISINSAFEZONE, None):
            attr[ATTR_TRACKER_ISINSAFEZONE] = watch_location_info[ATTR_TRACKER_ISINSAFEZONE]
        if watch_location_info.get(ATTR_TRACKER_SAFEZONELABEL, None):
            attr[ATTR_TRACKER_SAFEZONELABEL] = watch_location_info[ATTR_TRACKER_SAFEZONELABEL]

        attr['last Track'] = datetime.now()
        distanceToHome = self.get_location_distance((float(watch_location_info.get("lat")),
                                                     float(watch_location_info.get("lng"))))
        attr[ATTR_TRACKER_DISTOHOME] = "{} m".format(distanceToHome)
        if distanceToHome > attr[ATTR_TRACKER_RAD]:
            source_type = SOURCE_TYPE_GPS
        else:
            source_type = watch_location_info.get("locateTypec", await self._controller.getWatchLocateType(watch_id))

        await self._async_see(
            source_type=source_type,
            dev_id=slugify(self._controller.getWatchUserName(watch_id) + " Watch Tracker " + watch_id),
            gps=(float(watch_location_info.get("lat")), float(watch_location_info.get("lng"))),
            gps_accuracy=watch_location_info.get("rad"),
            battery=await self._controller.getWatchBattery(watch_id),
            host_name=f"{self._controller.getWatchUserName(watch_id)} Watch Tracker {watch_id}",
            attributes=attr,
            icon="mdi:watch",
            picture=(self._controller.getWatchUserIcon(watch_id)),
        )
