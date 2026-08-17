"""Language metadata - ISO 639-1 codes and display information."""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TypedDict


class LanguageCode(StrEnum):
    """ISO 639-1 language codes supported by the system."""

    ENGLISH = "en"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"
    PORTUGUESE = "pt"
    ITALIAN = "it"
    DUTCH = "nl"
    DANISH = "da"
    FINNISH = "fi"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    POLISH = "pl"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    TURKISH = "tr"
    GREEK = "el"
    CZECH = "cs"
    HUNGARIAN = "hu"
    ROMANIAN = "ro"
    UKRAINIAN = "uk"
    VIETNAMESE = "vi"
    THAI = "th"
    INDONESIAN = "id"
    MALAY = "ms"
    HEBREW = "he"
    SWAHILI = "sw"


# ============================================================
# Language Metadata
# ============================================================

@dataclass(frozen=True, slots=True)
class LanguageInfo:
    """Information about a language."""

    code: str
    name: str
    native_name: str
    icon: str = "🌐"  # Neutral language icon by default


# ============================================================
# Language Metadata (keyed by LanguageCode enum)
# ============================================================

_LANGUAGES: dict[LanguageCode, LanguageInfo] = {
    LanguageCode.ENGLISH: LanguageInfo(
        code="en",
        name="English",
        native_name="English",
        icon="🇬🇧",
    ),
    LanguageCode.FRENCH: LanguageInfo(
        code="fr",
        name="French",
        native_name="Français",
        icon="🌐",
    ),
    LanguageCode.GERMAN: LanguageInfo(
        code="de",
        name="German",
        native_name="Deutsch",
        icon="🌐",
    ),
    LanguageCode.SPANISH: LanguageInfo(
        code="es",
        name="Spanish",
        native_name="Español",
        icon="🌐",
    ),
    LanguageCode.PORTUGUESE: LanguageInfo(
        code="pt",
        name="Portuguese",
        native_name="Português",
        icon="🌐",
    ),
    LanguageCode.ITALIAN: LanguageInfo(
        code="it",
        name="Italian",
        native_name="Italiano",
        icon="🌐",
    ),
    LanguageCode.DUTCH: LanguageInfo(
        code="nl",
        name="Dutch",
        native_name="Nederlands",
        icon="🌐",
    ),
    LanguageCode.DANISH: LanguageInfo(
        code="da",
        name="Danish",
        native_name="Dansk",
        icon="🌐",
    ),
    LanguageCode.FINNISH: LanguageInfo(
        code="fi",
        name="Finnish",
        native_name="Suomi",
        icon="🌐",
    ),
    LanguageCode.SWEDISH: LanguageInfo(
        code="sv",
        name="Swedish",
        native_name="Svenska",
        icon="🌐",
    ),
    LanguageCode.NORWEGIAN: LanguageInfo(
        code="no",
        name="Norwegian",
        native_name="Norsk",
        icon="🌐",
    ),
    LanguageCode.POLISH: LanguageInfo(
        code="pl",
        name="Polish",
        native_name="Polski",
        icon="🌐",
    ),
    LanguageCode.RUSSIAN: LanguageInfo(
        code="ru",
        name="Russian",
        native_name="Русский",
        icon="🌐",
    ),
    LanguageCode.CHINESE: LanguageInfo(
        code="zh",
        name="Chinese",
        native_name="中文",
        icon="🌐",
    ),
    LanguageCode.JAPANESE: LanguageInfo(
        code="ja",
        name="Japanese",
        native_name="日本語",
        icon="🌐",
    ),
    LanguageCode.KOREAN: LanguageInfo(
        code="ko",
        name="Korean",
        native_name="한국어",
        icon="🌐",
    ),
    LanguageCode.ARABIC: LanguageInfo(
        code="ar",
        name="Arabic",
        native_name="العربية",
        icon="🌐",
    ),
    LanguageCode.HINDI: LanguageInfo(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        icon="🌐",
    ),
    LanguageCode.TURKISH: LanguageInfo(
        code="tr",
        name="Turkish",
        native_name="Türkçe",
        icon="🌐",
    ),
    LanguageCode.GREEK: LanguageInfo(
        code="el",
        name="Greek",
        native_name="Ελληνικά",
        icon="🌐",
    ),
    LanguageCode.CZECH: LanguageInfo(
        code="cs",
        name="Czech",
        native_name="Čeština",
        icon="🌐",
    ),
    LanguageCode.HUNGARIAN: LanguageInfo(
        code="hu",
        name="Hungarian",
        native_name="Magyar",
        icon="🌐",
    ),
    LanguageCode.ROMANIAN: LanguageInfo(
        code="ro",
        name="Romanian",
        native_name="Română",
        icon="🌐",
    ),
    LanguageCode.UKRAINIAN: LanguageInfo(
        code="uk",
        name="Ukrainian",
        native_name="Українська",
        icon="🌐",
    ),
    LanguageCode.VIETNAMESE: LanguageInfo(
        code="vi",
        name="Vietnamese",
        native_name="Tiếng Việt",
        icon="🌐",
    ),
    LanguageCode.THAI: LanguageInfo(
        code="th",
        name="Thai",
        native_name="ภาษาไทย",
        icon="🌐",
    ),
    LanguageCode.INDONESIAN: LanguageInfo(
        code="id",
        name="Indonesian",
        native_name="Bahasa Indonesia",
        icon="🌐",
    ),
    LanguageCode.MALAY: LanguageInfo(
        code="ms",
        name="Malay",
        native_name="Bahasa Melayu",
        icon="🌐",
    ),
    LanguageCode.HEBREW: LanguageInfo(
        code="he",
        name="Hebrew",
        native_name="עברית",
        icon="🌐",
    ),
    LanguageCode.SWAHILI: LanguageInfo(
        code="sw",
        name="Swahili",
        native_name="Kiswahili",
        icon="🌐",
    ),
}

# Expose as immutable mapping to prevent accidental mutation
LANGUAGES: MappingProxyType[LanguageCode, LanguageInfo] = MappingProxyType(_LANGUAGES)


# ============================================================
# Dashboard Language Type
# ============================================================

class DashboardLanguage(TypedDict):
    """Language data formatted for dashboard use."""

    code: str
    name: str
    native_name: str
    icon: str
    badge: str


# ============================================================
# Reverse Lookups (O(1))
# ============================================================

# Map name → LanguageCode (for fast reverse lookup)
_LANGUAGE_NAME_TO_CODE: dict[str, LanguageCode] = {}

for code, info in _LANGUAGES.items():
    _LANGUAGE_NAME_TO_CODE[info.name.lower().strip()] = code
    _LANGUAGE_NAME_TO_CODE[info.native_name.lower().strip()] = code


# ============================================================
# Helper Functions
# ============================================================

def normalize_language_code(code: str | None) -> str:
    """
    Normalize a language code to its base ISO 639-1 form.

    Examples:
        "EN" → "en"
        "en-US" → "en"
        "en_GB" → "en"
        "  Fr  " → "fr"
        None → "en"
    """
    if not code:
        return DEFAULT_LANGUAGE_CODE.value

    return (
        code.strip()
        .lower()
        .replace("_", "-")
        .split("-")[0]
    )


def validate_language(code: str) -> LanguageCode:
    """
    Validate and normalize a language code.

    Raises:
        ValueError: If the language code is not supported.
    """
    normalized = normalize_language_code(code)

    try:
        return LanguageCode(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported language code: {code}"
        ) from exc


def get_language_info(code: str) -> LanguageInfo | None:
    """Get language info for a given code."""
    try:
        lang_code = validate_language(code)
        return LANGUAGES.get(lang_code)
    except ValueError:
        return None


def get_language_name(code: str) -> str:
    """Get the English name of a language."""
    info = get_language_info(code)
    return info.name if info else code


def get_language_native_name(code: str) -> str:
    """Get the native name of a language."""
    info = get_language_info(code)
    return info.native_name if info else code


def get_language_icon(code: str) -> str:
    """Get the icon for a language."""
    info = get_language_info(code)
    return info.icon if info else "🌐"


def get_language_badge(code: str) -> str:
    """Get a badge string for a language (icon + code)."""
    info = get_language_info(code)
    if info:
        return f"{info.icon} {info.code.upper()}"
    return f"🌐 {code.upper() if code else 'UNK'}"


def is_supported_language(code: str) -> bool:
    """Check if a language code is supported."""
    try:
        validate_language(code)
        return True
    except ValueError:
        return False


def get_language_code_from_name(name: str) -> str | None:
    """Get the language code from a language name (O(1) lookup)."""
    if not name:
        return None
    cleaned = name.strip().lower()
    result = _LANGUAGE_NAME_TO_CODE.get(cleaned)
    return result.value if result else None


def get_all_language_codes() -> list[str]:
    """Get all supported language codes."""
    return sorted([code.value for code in LANGUAGES.keys()])


def get_all_language_names() -> list[str]:
    """Get all supported language names."""
    return sorted([info.name for info in LANGUAGES.values()])


def get_languages_for_dashboard() -> list[DashboardLanguage]:
    """Get language data formatted for dashboard use."""
    return [
        {
            "code": code.value,
            "name": info.name,
            "native_name": info.native_name,
            "icon": info.icon,
            "badge": f"{info.icon} {code.value.upper()}",
        }
        for code, info in sorted(_LANGUAGES.items(), key=lambda x: x[1].name)
    ]


# ============================================================
# Default Language
# ============================================================

DEFAULT_LANGUAGE_CODE = LanguageCode.ENGLISH


# ============================================================
# Export All
# ============================================================

__all__ = [
    "LanguageCode",
    "LanguageInfo",
    "DashboardLanguage",
    "LANGUAGES",
    "DEFAULT_LANGUAGE_CODE",
    "normalize_language_code",
    "validate_language",
    "get_language_info",
    "get_language_name",
    "get_language_native_name",
    "get_language_icon",
    "get_language_badge",
    "is_supported_language",
    "get_language_code_from_name",
    "get_all_language_codes",
    "get_all_language_names",
    "get_languages_for_dashboard",
]