from types import MappingProxyType
from typing import Any, cast

import pytest

from app.shared.languages import (
    DEFAULT_LANGUAGE_CODE,
    LANGUAGES,
    LanguageCode,
    LanguageInfo,
    get_all_language_codes,
    get_all_language_names,
    get_language_badge,
    get_language_code_from_name,
    get_language_icon,
    get_language_info,
    get_language_name,
    get_language_native_name,
    get_languages_for_dashboard,
    is_supported_language,
    normalize_language_code,
    validate_language,
)


def test_language_code_contains_supported_codes():
    assert LanguageCode.ENGLISH.value == "en"
    assert LanguageCode.FRENCH.value == "fr"
    assert LanguageCode.SWAHILI.value == "sw"
    assert len(LanguageCode) == 30


def test_language_info_has_default_icon():
    info = LanguageInfo(
        code="xx",
        name="Test",
        native_name="Test",
    )

    assert info.icon == "🌐"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "en"),
        ("", "en"),
        ("EN", "en"),
        ("  Fr  ", "fr"),
        ("en-US", "en"),
        ("en_GB", "en"),
        ("SW-ke", "sw"),
    ],
)
def test_normalize_language_code(value, expected):
    assert normalize_language_code(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("en", LanguageCode.ENGLISH),
        ("EN", LanguageCode.ENGLISH),
        ("en-US", LanguageCode.ENGLISH),
        ("  sw  ", LanguageCode.SWAHILI),
        ("fr-FR", LanguageCode.FRENCH),
    ],
)
def test_validate_language(value, expected):
    assert validate_language(value) is expected


def test_validate_language_rejects_unsupported_code():
    with pytest.raises(ValueError, match="Unsupported language code: xx"):
        validate_language("xx")


@pytest.mark.parametrize(
    ("code", "expected_name"),
    [
        ("en", "English"),
        ("fr", "French"),
        ("sw", "Swahili"),
    ],
)
def test_get_language_info_returns_language(code, expected_name):
    info = get_language_info(code)

    assert info is not None
    assert info.name == expected_name
    assert info.code == code


def test_get_language_info_returns_none_for_invalid_code():
    assert get_language_info("xx") is None


def test_language_name_native_name_and_icon():
    assert get_language_name("sw") == "Swahili"
    assert get_language_native_name("sw") == "Kiswahili"
    assert get_language_icon("sw") == "🌐"


def test_language_lookup_functions_fall_back_to_original_code():
    assert get_language_name("xx") == "xx"
    assert get_language_native_name("xx") == "xx"
    assert get_language_icon("xx") == "🌐"


def test_get_language_badge_for_supported_language():
    assert get_language_badge("en") == "🇬🇧 EN"
    assert get_language_badge("sw") == "🌐 SW"

def test_get_language_badge_for_unsupported_language():
    """Test language badge fallback for an unsupported language."""
    assert get_language_badge("xx") == "🌐 XX"

@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("en", True),
        ("EN", True),
        ("en-US", True),
        ("sw", True),
        ("xx", False),
    ],
)
def test_is_supported_language(code, expected):
    assert is_supported_language(code) is expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("English", "en"),
        ("english", "en"),
        ("  English  ", "en"),
        ("Kiswahili", "sw"),
        ("kIsWaHiLi", "sw"),
        ("Français", "fr"),
        ("Deutsch", "de"),
    ],
)
def test_get_language_code_from_name(name, expected):
    assert get_language_code_from_name(name) == expected


@pytest.mark.parametrize("name", ["", "   ", "Unknown Language"])
def test_get_language_code_from_name_returns_none_when_unknown(name):
    assert get_language_code_from_name(name) is None


def test_get_all_language_codes_returns_sorted_codes():
    codes = get_all_language_codes()

    assert len(codes) == 30
    assert codes == sorted(codes)
    assert "en" in codes
    assert "sw" in codes


def test_get_all_language_names_returns_sorted_names():
    names = get_all_language_names()

    assert len(names) == 30
    assert names == sorted(names)
    assert "English" in names
    assert "Swahili" in names


def test_get_languages_for_dashboard_returns_sorted_dashboard_data():
    languages = get_languages_for_dashboard()

    assert len(languages) == 30
    assert [language["name"] for language in languages] == sorted(
        language["name"] for language in languages
    )

    english = next(language for language in languages if language["code"] == "en")
    assert english == {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "icon": "🇬🇧",
        "badge": "🇬🇧 EN",
    }


def test_languages_is_immutable_mapping():
    assert isinstance(LANGUAGES, MappingProxyType)

    with pytest.raises(TypeError):
        cast(Any, LANGUAGES)[LanguageCode.ENGLISH] = LanguageInfo(
            code="en",
            name="Changed",
            native_name="Changed",
        )


def test_default_language_is_english():
    assert DEFAULT_LANGUAGE_CODE is LanguageCode.ENGLISH
