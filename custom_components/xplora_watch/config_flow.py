"""Config flow for Xplora® Watch Version 2."""
from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any

import voluptuous as vol
from pyxplora_api import pyxplora_api_async as PXA
from pyxplora_api.exception_classes import Error, LoginError, PhoneOrEmailFail
from pyxplora_api.status import UserContactType

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    STATE_OFF,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_COUNTRY_CODE,
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_HOME_RADIUS,
    CONF_HOME_SAFEZONE,
    CONF_LANGUAGE,
    CONF_MAPS,
    CONF_MESSAGE,
    CONF_OPENCAGE_APIKEY,
    CONF_PHONENUMBER,
    CONF_REMOVE_MESSAGE,
    CONF_SIGNIN_TYP,
    CONF_TIMEZONE,
    CONF_TYPES,
    CONF_USERLANG,
    CONF_WATCHES,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    HOME,
    HOME_SAFEZONE,
    LANGUAGES,
    MANUFACTURER,
    MAPS,
    SENSORS,
    SIGNIN,
)

_LOGGER = logging.getLogger(__name__)


DATA_SCHEMA_PHONE = {
    vol.Required(CONF_COUNTRY_CODE, default="+"): cv.string,
    vol.Required(CONF_PHONENUMBER): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_TIMEZONE, default="Europe/Berlin"): cv.string,
    vol.Required(CONF_USERLANG, default="de-DE"): cv.string,
    vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(LANGUAGES),
}
DATA_SCHEMA_EMAIL = {
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_TIMEZONE, default="Europe/Berlin"): cv.string,
    vol.Required(CONF_USERLANG, default="de-DE"): cv.string,
    vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(LANGUAGES),
}


async def validate_input(hass: core.HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    account = PXA.PyXploraApi()
    await account.init(signup=False)
    if not await account.checkEmailOrPhoneExist(
        UserContactType.EMAIL if data.get(CONF_EMAIL, None) else UserContactType.PHONE,
        email=data.get(CONF_EMAIL, None),
        countryCode=data.get(CONF_COUNTRY_CODE, None),
        phoneNumber=data.get(CONF_PHONENUMBER, None),
    ):
        raise PhoneOrEmailFail()

    account = PXA.PyXploraApi(
        countrycode=data.get(CONF_COUNTRY_CODE, None),
        phoneNumber=data.get(CONF_PHONENUMBER, None),
        password=data[CONF_PASSWORD],
        userLang=data[CONF_USERLANG],
        timeZone=data[CONF_TIMEZONE],
        email=data.get(CONF_EMAIL, None),
    )

    try:
        await account.init()
    except LoginError as err:
        raise LoginError(err.error_message)

    # Return info that you want to store in the config entry.
    return {"title": f"{MANUFACTURER}"}


def validate_options_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    errors = {}
    key: str = user_input[CONF_OPENCAGE_APIKEY]
    maps = user_input[CONF_MAPS]

    if maps == MAPS[1] and len(key) == 0:
        errors["base"] = "api_key_error"

    if not user_input[CONF_WATCHES]:
        errors["base"] = "no_watch"

    for watch in user_input[CONF_WATCHES]:
        for i in range(1, len(user_input[CONF_WATCHES]) + 1):
            user_input_watches = user_input.get(f"{CONF_WATCHES}_{i}")
            if not user_input_watches:
                errors["base"] = "friendly_name_error"
                continue

            if "=" not in user_input_watches and len(user_input_watches) != len(watch):
                errors["base"] = "friendly_name_error"

    if not user_input[CONF_TYPES]:
        errors["base"] = "no_sensor"

    # Return info that you want to store in the config entry.
    return errors


class XploraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xplora® Watch Version 2."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return XploraOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        return self.async_show_menu(step_id="user", menu_options=["user_email", "user_phone"])

    async def async_step_user_phone(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:

            unique_id = f"{user_input[CONF_PHONENUMBER]}"

            self.entry = await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            info = None
            try:
                info = await validate_input(self.hass, user_input)
            except PhoneOrEmailFail as e:
                _LOGGER.exception(e)
                errors["base"] = "phone_email_invalid"
            except LoginError as e:
                _LOGGER.exception(e)
                errors["base"] = "pass_invalid"
            except Error as e:
                _LOGGER.exception(e)
                errors["base"] = "cannot_connect"

            if info:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user_phone", data_schema=vol.Schema(DATA_SCHEMA_PHONE), errors=errors, last_step=False
        )

    async def async_step_user_email(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:

            unique_id = f"{user_input[CONF_EMAIL]}"

            self.entry = await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            info = None
            try:
                info = await validate_input(self.hass, user_input)
            except PhoneOrEmailFail as e:
                _LOGGER.exception(e)
                errors["base"] = "phone_email_invalid"
            except LoginError as e:
                _LOGGER.exception(e)
                errors["base"] = "pass_invalid"
            except Error as e:
                _LOGGER.exception(e)
                errors["base"] = "cannot_connect"

            if info:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user_email", data_schema=vol.Schema(DATA_SCHEMA_EMAIL), errors=errors, last_step=False
        )


class XploraOptionsFlowHandler(OptionsFlow):
    """Handle a option flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle options flow."""
        errors: dict[str, str] = {}
        controller = PXA.PyXploraApi(
            self.config_entry.data.get(CONF_COUNTRY_CODE, None),
            self.config_entry.data.get(CONF_PHONENUMBER, None),
            self.config_entry.data.get(CONF_PASSWORD, None),
            self.config_entry.data.get(CONF_USERLANG, None),
            self.config_entry.data.get(CONF_TIMEZONE, None),
            email=self.config_entry.data.get(CONF_EMAIL, None),
        )
        await controller.init()
        watches = await controller.setDevices()
        _options = self.config_entry.options

        schema = OrderedDict()
        schema[vol.Required(CONF_WATCHES, default=_options.get(CONF_WATCHES, watches))] = cv.multi_select(watches)
        i = 1
        for watch in watches:
            schema[vol.Optional(f"{CONF_WATCHES}_{i}", default=_options.get(f"{CONF_WATCHES}_{i}", watch))] = cv.string
            i += 1

        language = _options.get(CONF_LANGUAGE, self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))

        signin_typ = [
            SIGNIN.get(language, DEFAULT_LANGUAGE).get(CONF_EMAIL)
            if CONF_EMAIL in self.config_entry.data
            else SIGNIN.get(language, DEFAULT_LANGUAGE).get(CONF_PHONENUMBER)
        ]

        _home_zone = self.hass.states.get(HOME).attributes
        options = vol.Schema(
            {
                vol.Optional(CONF_SIGNIN_TYP, default=signin_typ[0]): vol.In(signin_typ),
                **schema,
                vol.Required(CONF_LANGUAGE, default=language): vol.In(LANGUAGES),
                vol.Required(CONF_MAPS, default=_options.get(CONF_MAPS, MAPS[0])): vol.In(MAPS),
                vol.Optional(CONF_OPENCAGE_APIKEY, default=_options.get(CONF_OPENCAGE_APIKEY, "")): cv.string,
                vol.Required(CONF_SCAN_INTERVAL, default=_options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=9999)
                ),
                vol.Required(CONF_HOME_SAFEZONE, default=_options.get(CONF_HOME_SAFEZONE, STATE_OFF)): vol.In(
                    HOME_SAFEZONE.get(language, DEFAULT_LANGUAGE)
                ),
                vol.Required(
                    CONF_HOME_LATITUDE, default=_options.get(CONF_HOME_LATITUDE, _home_zone[ATTR_LATITUDE])
                ): cv.latitude,
                vol.Required(
                    CONF_HOME_LONGITUDE, default=_options.get(CONF_HOME_LONGITUDE, _home_zone[ATTR_LONGITUDE])
                ): cv.longitude,
                vol.Required(
                    CONF_HOME_RADIUS, default=_options.get(CONF_HOME_RADIUS, _home_zone[CONF_RADIUS])
                ): cv.positive_int,
                vol.Required(CONF_TYPES, default=_options.get(CONF_TYPES, [])): cv.multi_select(
                    SENSORS.get(language, DEFAULT_LANGUAGE)
                ),
                vol.Required(CONF_MESSAGE, default=_options.get(CONF_MESSAGE, 10)): cv.positive_int,
                vol.Required(CONF_REMOVE_MESSAGE, default=_options.get(CONF_REMOVE_MESSAGE, False)): cv.boolean,
            }
        )

        if user_input is not None:
            errors = validate_options_input(user_input)

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=options, errors=errors)
