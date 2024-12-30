"""Const schema for Xplora® Watch Version 2."""

from __future__ import annotations

from homeassistant.const import CONF_COUNTRY_CODE, CONF_EMAIL, CONF_LANGUAGE, CONF_PASSWORD
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import voluptuous as vol

from .const import CONF_PHONENUMBER, CONF_TIMEZONE, CONF_USERLANG, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, XPLORA_USER_LANGS

DEFAULT_DATA_SCHEMA = {
    vol.Required(CONF_PASSWORD): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
    vol.Required(CONF_TIMEZONE, default="Europe/Berlin"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
    vol.Required(CONF_USERLANG, default="en-GB"): SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(
                    value=language_value,
                    label=language_key,
                )
                for language_dict in XPLORA_USER_LANGS
                for language_key, language_value in language_dict.items()
            ],
            multiple=False,
            mode=SelectSelectorMode.DROPDOWN,
        )
    ),
    vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(
                    value=language_key,
                    label=language_value,
                )
                for language_dict in SUPPORTED_LANGUAGES
                for language_key, language_value in language_dict.items()
            ],
            multiple=False,
            mode=SelectSelectorMode.DROPDOWN,
        )
    ),
}

DATA_SCHEMA_PHONE = {
    vol.Required(CONF_COUNTRY_CODE, default="+"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
    vol.Required(CONF_PHONENUMBER): TextSelector(TextSelectorConfig(type=TextSelectorType.TEL)),
    **DEFAULT_DATA_SCHEMA,
}
DATA_SCHEMA_EMAIL = {
    vol.Required(CONF_EMAIL): TextSelector(TextSelectorConfig(type=TextSelectorType.EMAIL)),
    **DEFAULT_DATA_SCHEMA,
}
