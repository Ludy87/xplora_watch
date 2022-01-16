"""Support for xplora watch tracking."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
import logging

from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
    SOURCE_TYPE_GPS,
)
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from .const import (
    DOMAIN,
    CONF_SCAN_INTERVAL,
    DATA_XPLORA,
    XPLORA_CONTROLLER,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TRACKER_LAT,
    DEVICE_TRACKER_LNG,
    DEVICE_TRACKER_RAD,
    DEVICE_TRACKER_COUNTRY,
    DEVICE_TRACKER_COUNTRY_ABBR,
    DEVICE_TRACKER_PROVINCE,
    DEVICE_TRACKER_CITY,
    DEVICE_TRACKER_ADDR,
    DEVICE_TRACKER_POI,
    DEVICE_TRACKER_ISINSAFEZONE,
    DEVICE_TRACKER_SAFEZONELABEL,
)
from .sensor_const import bat
from pyxplora_api import pyxplora_api_async as PXA

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

# from . import DOMAIN, TRACKER_UPDATE
TRACKER_UPDATE = 60

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
SCAN_INTERVAL = DEFAULT_SCAN_INTERVAL


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Configure a dispatcher connection based on a config entry."""

    @callback
    def _receive_data(device, latitude, longitude, battery, accuracy, attrs):
        """Receive set location."""
        if device in hass.data[DOMAIN]["devices"]:
            return

        hass.data[DOMAIN]["devices"].add(device)

        async_add_entities(
            [WatchEntity(device, latitude, longitude, battery, accuracy, attrs)]
        )

    hass.data[DOMAIN]["unsub_device_tracker"][
        entry.entry_id
    ] = async_dispatcher_connect(hass, TRACKER_UPDATE, _receive_data)

    # Restore previously loaded devices
    dev_reg = await device_registry.async_get_registry(hass)
    dev_ids = {
        identifier[1]
        for device in dev_reg.devices.values()
        for identifier in device.identifiers
        if identifier[0] == DOMAIN
    }
    if not dev_ids:
        return

    entities = []
    for dev_id in dev_ids:
        hass.data[DOMAIN]["devices"].add(dev_id)
        entity = WatchEntity(dev_id, None, None, None, None, None)
        entities.append(entity)

    async_add_entities(entities)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    async_see: Callable[..., Awaitable[None]],
    discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Validate the configuration and return a Xplora scanner."""

    api: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]

    # api = controller

    scanner = WatchScanner(
        api,
        hass,
        async_see,
        config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL),
    )

    return await scanner.async_init()


class WatchScanner:
    """Define an object to retrieve Traccar data."""

    def __init__(
        self,
        api,
        hass,
        async_see,
        scan_interval,
        # max_accuracy,
        # skip_accuracy_on,
        # custom_attributes,
        # event_types,
    ):
        """Initialize."""

        # self._custom_attributes = custom_attributes
        self._scan_interval = scan_interval
        self._async_see = async_see
        self._api = api
        self.connected = False
        self._hass = hass
        self._watch_location = None
        # self._max_accuracy = max_accuracy
        # self._skip_accuracy_on = skip_accuracy_on

    async def async_init(self):
        """Further initialize connection to Xplora API."""
        await self._api.init_async()
        username = await self._api.getWatchUserName_async()
        if username is None:
            _LOGGER.error("Can not connect to Xplora API")
            return False

        await self._async_update()
        async_track_time_interval(self._hass, self._async_update, self._scan_interval)
        return True

    async def _async_update(self, now=None):
        """Update info from Xplora API."""
        if not self.connected:
            _LOGGER.debug("Testing connection to Xplora API")
            self.connected = await self._api.getWatchUserID_async() is not None
            #        if self.connected is not None:
            # self.connected = self._api.connected
            if self.connected:
                _LOGGER.info("Connection to Xplora API restored")
            else:
                return
        _LOGGER.debug("Updating device data")
        self._watch_location = await self._api.getWatchLastLocation_async()
        self._hass.async_create_task(self.import_device_data())
        # self.connected = self._api.connected

    async def import_device_data(self):
        """Import device data from Xplora API."""
        # for device_unique_id in self._api.device_info:
        device_info = self._watch_location
        # device = None
        attr = {}
        #     skip_accuracy_filter = False

        # attr[ATTR_TRACKER] = "xplora"
        if device_info.get("lat") is not None:
            attr[DEVICE_TRACKER_LAT] = device_info["lat"]
        if device_info.get("lng") is not None:
            attr[DEVICE_TRACKER_LNG] = device_info["lng"]
        if device_info.get("rad") is not None:
            attr[DEVICE_TRACKER_RAD] = device_info["rad"]
        if device_info.get("country") is not None:
            attr[DEVICE_TRACKER_COUNTRY] = device_info["country"]
        if device_info.get("countryAbbr") is not None:
            attr[DEVICE_TRACKER_COUNTRY_ABBR] = device_info["countryAbbr"]
        if device_info.get("province") is not None:
            attr[DEVICE_TRACKER_PROVINCE] = device_info["province"]
        if device_info.get("city") is not None:
            attr[DEVICE_TRACKER_CITY] = device_info["city"]
        if device_info.get("addr") is not None:
            attr[DEVICE_TRACKER_ADDR] = device_info["addr"]
        if device_info.get("poi") is not None:
            attr[DEVICE_TRACKER_POI] = device_info["poi"]
        if device_info.get("isInSafeZone") is not None:
            attr[DEVICE_TRACKER_ISINSAFEZONE] = device_info["isInSafeZone"]
        if device_info.get("safeZoneLabel") is not None:
            attr[DEVICE_TRACKER_SAFEZONELABEL] = device_info["safeZoneLabel"]

            await self._async_see(
                dev_id=slugify(self._api.watch.get("name")),
                gps=(device_info.get("lat"), device_info.get("lng")),
                gps_accuracy=device_info.get("rad"),
                battery=device_info.get("battery"),
                attributes=attr,
            )


class WatchEntity(TrackerEntity, RestoreEntity):
    """Represent a tracked device."""

    def __init__(self, device, latitude, longitude, battery, accuracy, attributes):
        """Set up Geofency entity."""
        self._accuracy = accuracy
        self._attributes = attributes
        self._name = device
        self._battery = battery
        self._latitude = latitude
        self._longitude = longitude
        self._unsub_dispatcher = None
        self._unique_id = device

    @property
    def battery_level(self):
        """Return battery value of the device."""
        return self._battery

    @property
    def extra_state_attributes(self):
        """Return device specific attributes."""
        return self._attributes

    @property
    def latitude(self):
        """Return latitude value of the device."""
        return self._latitude

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._longitude

    @property
    def location_accuracy(self):
        """Return the gps accuracy of the device."""
        return self._accuracy

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._unique_id

    @property
    def device_info(self):
        """Return the device info."""
        return {"name": self._name, "identifiers": {(DOMAIN, self._unique_id)}}

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    async def async_added_to_hass(self):
        """Register state update callback."""
        await super().async_added_to_hass()
        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass, TRACKER_UPDATE, self._async_receive_data
        )

        # don't restore if we got created with data
        if self._latitude is not None or self._longitude is not None:
            return

        if (state := await self.async_get_last_state()) is None:
            self._latitude = None
            self._longitude = None
            self._accuracy = None
            self._attributes = {
                DEVICE_TRACKER_COUNTRY: None,
                DEVICE_TRACKER_COUNTRY_ABBR: None,
                DEVICE_TRACKER_ISINSAFEZONE: None,
            }
            self._battery = None
            return

        attr = state.attributes
        self._latitude = attr.get(DEVICE_TRACKER_LAT)
        self._longitude = attr.get(DEVICE_TRACKER_LNG)
        # self._accuracy = attr.get(ATTR_ACCURACY)
        self._attributes = {
            DEVICE_TRACKER_COUNTRY: attr.get(DEVICE_TRACKER_COUNTRY),
            DEVICE_TRACKER_COUNTRY_ABBR: attr.get(DEVICE_TRACKER_COUNTRY_ABBR),
            DEVICE_TRACKER_ISINSAFEZONE: attr.get(DEVICE_TRACKER_ISINSAFEZONE),
        }
        # self._battery = attr.get(ATTR_BATTERY)
        self._battery = 1

    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        await super().async_will_remove_from_hass()
        self._unsub_dispatcher()

    @callback
    def _async_receive_data(
        self, device, latitude, longitude, battery, accuracy, attributes
    ):
        """Mark the device as seen."""
        if device != self.name:
            return

        self._latitude = latitude
        self._longitude = longitude
        self._battery = battery
        self._accuracy = accuracy
        self._attributes.update(attributes)
        self.async_write_ha_state()
