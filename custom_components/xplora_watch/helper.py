"""HelperClasses Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from geopy import distance

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    HOME,
    STR_READ_MESSAGE_SERVICE,
    STR_SEE_SERVICE,
    STR_SEND_MESSAGE_SERVICE,
    STR_SHUTDOWN_SERVICE,
)

_LOGGER = logging.getLogger(__name__)


def get_location_distance_meter(hass: HomeAssistant, lat_lng: tuple[float, float]) -> int:
    home_zone = hass.states.get(HOME).attributes
    return int(
        distance.distance(
            (home_zone[ATTR_LATITUDE], home_zone[ATTR_LONGITUDE]),
            lat_lng,
        ).m
    )


def is_distance_in_radius(home_lat_lng: tuple[float, float], lat_lng: tuple[float, float], radius: int) -> bool:
    if radius >= int(distance.distance(home_lat_lng, lat_lng).m):
        return True
    else:
        return False


def create_service_yaml_file(hass: HomeAssistant, entry: ConfigEntry, watches: list[str]) -> None:
    path = hass.config.path("custom_components/xplora_watch/services.yaml")
    _LOGGER.debug("services.yaml path: %s", path)
    try:
        language = entry.options.get(CONF_LANGUAGE, entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        with open(path, "w+") as f:
            f.write(STR_SEND_MESSAGE_SERVICE.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

            f.write(STR_SEE_SERVICE.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

            f.write(STR_READ_MESSAGE_SERVICE.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

            f.write(STR_SHUTDOWN_SERVICE.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

    except IOError:
        _LOGGER.exception("Error writing service definition to path '%s'", path)
