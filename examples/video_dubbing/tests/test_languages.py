"""Language table: any Speak∩Translate code; never hardcode demo langs in callers."""

from __future__ import annotations

import pytest

from bodhan_dub.config.languages import (
    LANGUAGE_TABLE,
    get_language,
    list_supported_codes,
    resolve_languages,
)
from bodhan_dub.errors import UnsupportedLanguageError


def test_table_covers_common_indic_codes() -> None:
    for code in ("hi", "ta", "bn", "te", "kn", "ml", "mr", "gu", "pa", "or", "as", "ur"):
        assert code in LANGUAGE_TABLE


def test_resolve_langs_csv() -> None:
    infos = resolve_languages("hi, ta, bn")
    assert [i.code for i in infos] == ["hi", "ta", "bn"]


def test_resolve_dedupes() -> None:
    infos = resolve_languages("hi,hi,ta")
    assert [i.code for i in infos] == ["hi", "ta"]


def test_unsupported_lists_supported() -> None:
    with pytest.raises(UnsupportedLanguageError) as exc:
        get_language("xx")
    assert "hi" in str(exc.value)
    assert list_supported_codes() == sorted(LANGUAGE_TABLE)


def test_codemix_flag_present() -> None:
    assert get_language("hi").supports_codemix is True
