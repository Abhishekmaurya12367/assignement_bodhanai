"""Configuration: env settings, language table, pricing."""

from bodhan_dub.config.languages import (
    LANGUAGE_TABLE,
    LanguageInfo,
    default_voice_for,
    get_language,
    list_supported_codes,
    resolve_languages,
)
from bodhan_dub.config.pricing import Pricing
from bodhan_dub.config.settings import Settings, get_settings

__all__ = [
    "LANGUAGE_TABLE",
    "LanguageInfo",
    "Pricing",
    "Settings",
    "default_voice_for",
    "get_language",
    "get_settings",
    "list_supported_codes",
    "resolve_languages",
]
