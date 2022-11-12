"""HelperClasses Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from geopy import distance

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import CONF_LANGUAGE, DEFAULT_LANGUAGE, HOME, STR_READ_MESSAGE, STR_SEE, STR_SEND_MESSAGE

_LOGGER = logging.getLogger(__name__)


def get_location_distance_meter(hass: HomeAssistant, lat_lng: tuple[float, float]) -> int:
    home_zone = hass.states.get(HOME).attributes
    return int(
        distance.distance(
            (home_zone[ATTR_LATITUDE], home_zone[ATTR_LONGITUDE]),
            lat_lng,
        ).m
    )


def get_location_distance(home_lat_lng: tuple[float, float], lat_lng: tuple[float, float], radius: int) -> bool:
    if radius >= int(distance.distance(home_lat_lng, lat_lng).m):
        return True
    else:
        return False


def set_service_yaml(hass: HomeAssistant, entry: ConfigEntry, watches: list[str]) -> None:
    path = hass.config.path("custom_components/xplora_watch/services.yaml")
    _LOGGER.debug("services.yaml path: %s", path)
    try:
        language = entry.options.get(CONF_LANGUAGE, entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        with open(path, "w+") as f:
            f.write(STR_SEND_MESSAGE.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

            f.write(STR_SEE.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

            f.write(STR_READ_MESSAGE.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

    except IOError:
        _LOGGER.exception("Error writing service definition to path '%s'", path)
