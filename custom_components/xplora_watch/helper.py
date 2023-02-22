"""HelperClasses Xplora® Watch Version 2."""
from __future__ import annotations

import base64
import logging
import os
import shutil

from geopy import distance
from pydub import AudioSegment

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    DOMAIN,
    HOME,
    STR_DELETE_MESSAGE_FROM_APP,
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


def encoded_base64_string_to_file(hass: HomeAssistant, base64_string: str, file_name: str, file_type: str, file_dir: str):
    media_path = hass.config.path(f"www/{file_dir}")
    if not os.path.exists(f"{media_path}/{file_name}.{file_type}"):
        try:
            decoded_data = base64.b64decode(base64_string.encode())
            with open(f"{media_path}/{file_name}.{file_type}", "wb") as f:
                f.write(decoded_data)
        except AttributeError:
            return


def encoded_base64_string_to_mp3_file(hass: HomeAssistant, base64_string: str, file_name: str):
    media_path = hass.config.path("www/voice")
    if not os.path.exists(f"{media_path}/{file_name}.mp3"):
        decoded_data = base64.b64decode(base64_string.encode())
        with open(f"{media_path}/{file_name}.amr", "wb") as f:
            f.write(decoded_data)
        if os.path.exists(f"{media_path}/{file_name}.amr"):
            sound = AudioSegment.from_file(f"{media_path}/{file_name}.amr", format="amr")
            sound.export(f"{media_path}/{file_name}.mp3", format="mp3")
            os.remove(f"{media_path}/{file_name}.amr")


async def create_www_directory(hass: HomeAssistant):
    paths = [
        hass.config.path("www/image"),  # http://homeassistant.local:8123/local/image/<filename>.jpeg
        hass.config.path("www/video"),  # http://homeassistant.local:8123/local/video/<filename>.mp4
        hass.config.path("www/video/thumb"),  # http://homeassistant.local:8123/local/video/thumb/<filename>.jpeg
        hass.config.path("www/voice"),  # http://homeassistant.local:8123/local/voice/<filename>.mp3
        hass.config.path(f"www/{DOMAIN}"),
    ]

    def mkdir() -> None:
        for path in paths:
            if not os.path.exists(path):
                _LOGGER.debug("Creating directory: %s" % path)
                os.makedirs(path, exist_ok=True)

    await hass.async_add_executor_job(mkdir)


def move_file(hass: HomeAssistant):
    src_path = hass.config.path("custom_components/xplora_watch/emojis")
    dst_path = hass.config.path(f"www/{DOMAIN}")
    if os.path.exists(src_path):
        if os.path.exists(f"{dst_path}/emojis"):
            shutil.rmtree(f"{dst_path}/emojis")
        shutil.move(src_path, dst_path)


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

            f.write(STR_DELETE_MESSAGE_FROM_APP.get(language, DEFAULT_LANGUAGE))
            for watch in watches:
                f.write(f'            - "{watch}"\n')

    except IOError:
        _LOGGER.exception("Error writing service definition to path '%s'", path)
