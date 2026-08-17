"""
Language detection for job postings.

This module provides language detection for job titles and descriptions
during the ETL enrichment process. It uses lingua-language-detector
for fast, accurate detection of European languages.

Design decisions:
- Detection is performed during ETL (batch, cheap operation)
- Only language code is stored (ISO 639-1)
- Defaults to English ONLY if detection completely fails or text is too short
- No translation is performed here - translation is on-demand in the API
- LRU cache prevents unbounded memory growth
- Minimum confidence threshold is low to detect non-English languages
- detect() and detect_with_confidence() use the same internal logic
- Cache stores (language, confidence) tuple to preserve confidence
- Stable cache key using SHA1 hash of normalized text
- Specifically designed for lingua-language-detector 2.2.0+
"""

import hashlib
import logging
import re
from collections import OrderedDict
from typing import Optional, Tuple, TYPE_CHECKING

# Import lingua - specifically for v2.2.0+
if TYPE_CHECKING:
    from lingua import Language, LanguageDetectorBuilder, ConfidenceValue
else:
    try:
        from lingua import Language, LanguageDetectorBuilder, ConfidenceValue
    except ImportError:
        # Provide dummy types for development when library is not installed
        class Language:  # type: ignore
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
            # Norwegian is split into two written standards
            BOKMAL = "nb"
            NYNORSK = "nn"
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
            iso_code_639_1 = None

        class LanguageDetectorBuilder:  # type: ignore
            @classmethod
            def from_languages(cls, *args):
                return cls()
            
            def build(self):
                return None

        class ConfidenceValue:  # type: ignore
            language = None
            value = 0.0

        # Re-raise with clear error message for runtime
        import sys
        if not TYPE_CHECKING:
            raise ImportError(
                "lingua-language-detector is required. "
                "Install it with: pip install lingua-language-detector"
            )

from app.shared.languages import DEFAULT_LANGUAGE_CODE, LanguageCode

logger = logging.getLogger(__name__)

# ============================================================
# German Job Posting Patterns
# ============================================================

GERMAN_SUFFIX_PATTERNS = [
    r'\(m/w/d\)',
    r'\(w/m/d\)',
    r'\(d/w/m\)',
    r'\(m/w\)',
    r'\(w/m\)',
    r'\(mwd\)',
    r'\(wmd\)',
    r'\(dwm\)',
    r'\(m/w/d\)',
    r'\(w/m/d\)',
    r'\(d/w/m\)',
]

# Compile patterns for performance
GERMAN_SUFFIX_REGEX = re.compile('|'.join(GERMAN_SUFFIX_PATTERNS), re.IGNORECASE)


def clean_text_for_detection(text: str) -> str:
    """
    Remove German job posting conventions before language detection.
    
    German job postings often include gender diversity indicators like
    "(m/w/d)" which can confuse language detection. This function
    removes these patterns to improve detection accuracy.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text with German suffixes removed
    """
    if not text:
        return text
    
    # Remove German suffixes
    cleaned = GERMAN_SUFFIX_REGEX.sub('', text)
    
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


class LanguageDetector:
    """
    Fast, deterministic language detector for job postings.
    
    Uses lingua-language-detector 2.2.0+ which is more accurate than 
    langdetect and faster for European languages.
    
    Example:
        detector = LanguageDetector()
        language = detector.detect("Senior Software Engineer")
        # returns LanguageCode.ENGLISH
    """

    # Minimum text length to attempt detection
    MIN_TEXT_LENGTH = 5

    # Minimum confidence threshold (0.0 - 1.0)
    # LOW threshold ensures non-English languages are detected
    # Even with low confidence, we use the detected language
    MIN_CONFIDENCE = 0.25  # Changed from 0.55 to detect non-English

    # Maximum cache size
    MAX_CACHE_SIZE = 5000

    # Languages supported by the detector
    # Note: In Lingua 2.2.0, Norwegian is split into Bokmål and Nynorsk
    SUPPORTED_LANGUAGES = [
        Language.ENGLISH,
        Language.FRENCH,
        Language.GERMAN,
        Language.SPANISH,
        Language.PORTUGUESE,
        Language.ITALIAN,
        Language.DUTCH,
        Language.DANISH,
        Language.FINNISH,
        Language.SWEDISH,
        # Norwegian - two written standards in Lingua 2.2.0
        Language.BOKMAL,
        Language.NYNORSK,
        Language.POLISH,
        Language.RUSSIAN,
        Language.CHINESE,
        Language.JAPANESE,
        Language.KOREAN,
        Language.ARABIC,
        Language.HINDI,
        Language.TURKISH,
        Language.GREEK,
        Language.CZECH,
        Language.HUNGARIAN,
        Language.ROMANIAN,
        Language.UKRAINIAN,
        Language.VIETNAMESE,
        Language.THAI,
        Language.INDONESIAN,
        Language.MALAY,
        Language.HEBREW,
        Language.SWAHILI,
    ]

    # Precomputed list of supported language codes
    SUPPORTED_LANGUAGE_CODES: Tuple[str, ...] = tuple(
        lang.iso_code_639_1.name.lower()
        for lang in SUPPORTED_LANGUAGES
        if hasattr(lang, "iso_code_639_1") and lang.iso_code_639_1 is not None
    )

    def __init__(self):
        """Initialize the language detector with supported languages."""
        self._build_detector()
        # LRU cache using OrderedDict - stores (LanguageCode, confidence)
        self._cache: OrderedDict[str, Tuple[LanguageCode, float]] = OrderedDict()
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._cache_evictions: int = 0

    def _build_detector(self) -> None:
        """Build the Lingua language detector."""
        try:
            self.detector = LanguageDetectorBuilder.from_languages(
                *self.SUPPORTED_LANGUAGES
            ).build()
            logger.info(
                "Language detector built with %d languages",
                len(self.SUPPORTED_LANGUAGES),
            )
        except Exception as e:
            logger.error("Failed to build language detector: %s", e)
            raise RuntimeError(f"Language detector initialization failed: {e}") from e

    def _get_cache_key(self, text: str) -> str:
        """Generate a stable cache key using SHA1 hash."""
        normalized = text.casefold()
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> Optional[Tuple[LanguageCode, float]]:
        """Get value from cache and update LRU order."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache_hits += 1
            return self._cache[key]
        self._cache_misses += 1
        return None

    def _cache_set(self, key: str, value: Tuple[LanguageCode, float]) -> None:
        """Set value in cache with LRU eviction."""
        if key in self._cache:
            self._cache[key] = value
            self._cache.move_to_end(key)
        else:
            self._cache[key] = value
            if len(self._cache) > self.MAX_CACHE_SIZE:
                self._cache.popitem(last=False)
                self._cache_evictions += 1

    def _should_detect(self, text: str) -> bool:
        """Check if text is long enough for detection."""
        return bool(text and len(text.strip()) >= self.MIN_TEXT_LENGTH)

    def _to_language_code(self, detected_lang: "Language") -> Optional[LanguageCode]:
        """Convert Lingua Language to our LanguageCode enum."""
        try:
            iso = detected_lang.iso_code_639_1
            if iso is None:
                return None
            lang_code = iso.name.lower()
            return LanguageCode(lang_code)
        except (ValueError, AttributeError):
            return None

    def _get_confidence(self, text: str) -> float:
        """
        Get confidence scores using lingua-language-detector 2.2.0+ API.
        
        In 2.2.0+, compute_language_confidence_values() returns a list of
        ConfidenceValue objects with .language and .value attributes.
        """
        try:
            # Use the 2.2.0+ API
            confidence_values = self.detector.compute_language_confidence_values(text)
            
            if not confidence_values:
                # Return 0.5 as default - don't assume English
                return 0.5
            
            # Find the highest confidence value
            best = max(confidence_values, key=lambda cv: cv.value)
            return best.value
            
        except Exception as e:
            logger.debug("Confidence calculation failed: %s", e)
            # Return 0.5 as default - don't assume English
            return 0.5

    def _detect_internal(self, text: str) -> Tuple[LanguageCode, float]:
        """
        Internal detection method - returns both language and confidence.
        
        This is the single source of truth for detection logic.
        """
        # Clean text before detection to remove German job posting conventions
        cleaned_text = clean_text_for_detection(text)
        
        if not self._should_detect(cleaned_text):
            logger.debug("Text too short for language detection, defaulting to English")
            return (DEFAULT_LANGUAGE_CODE, 0.0)

        cache_key = self._get_cache_key(cleaned_text)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            # Detect language
            detected = self.detector.detect_language_of(cleaned_text)

            if detected is None:
                logger.debug("No language detected, defaulting to English")
                default_entry = (DEFAULT_LANGUAGE_CODE, 0.0)
                self._cache_set(cache_key, default_entry)
                return default_entry

            # Get confidence
            confidence = self._get_confidence(cleaned_text)
            
            # Convert to LanguageCode
            language = self._to_language_code(detected)

            if language is None:
                logger.debug("No ISO code available, defaulting to English")
                default_entry = (DEFAULT_LANGUAGE_CODE, 0.0)
                self._cache_set(cache_key, default_entry)
                return default_entry

            # ✅ REMOVED: Confidence threshold check
            # We now always use the detected language, regardless of confidence
            
            entry = (language, confidence)
            self._cache_set(cache_key, entry)
            logger.debug(
                "Detected language: %s (conf: %.2f) for text: %s...",
                language.value,
                confidence,
                cleaned_text[:50],
            )
            return entry

        except Exception as e:
            logger.exception("Unexpected error in language detection: %s", e)
            default_entry = (DEFAULT_LANGUAGE_CODE, 0.0)
            self._cache_set(cache_key, default_entry)
            return default_entry

    def detect(self, text: str) -> LanguageCode:
        """Detect the language of a text string."""
        language, _ = self._detect_internal(text)
        return language

    def detect_with_confidence(self, text: str) -> Tuple[LanguageCode, float]:
        """Detect the language of a text string with confidence score."""
        return self._detect_internal(text)

    def is_english(self, text: str) -> bool:
        """Check if text is likely English."""
        return self.detect(text) == LanguageCode.ENGLISH

    def is_english_with_confidence(self, text: str) -> Tuple[bool, float]:
        """Check if text is likely English with confidence score."""
        language, confidence = self.detect_with_confidence(text)
        return language == LanguageCode.ENGLISH, confidence

    def get_supported_languages(self) -> Tuple[str, ...]:
        """Get list of languages supported by the detector."""
        codes = []
        for lang in self.SUPPORTED_LANGUAGES:
            iso = getattr(lang, "iso_code_639_1", None)
            if iso is not None:
                codes.append(iso.name.lower())
        return tuple(codes)

    def clear_cache(self) -> None:
        """Clear the detection cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_evictions = 0
        logger.debug("Language detection cache cleared (%d entries)", cache_size)

    def get_cache_size(self) -> int:
        """Get the current cache size."""
        return len(self._cache)

    def get_cache_stats(self) -> dict[str, int | float]:
        """Get cache statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = round((self._cache_hits / total * 100), 2) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.MAX_CACHE_SIZE,
            "used_percent": round((len(self._cache) / self.MAX_CACHE_SIZE) * 100, 2),
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "evictions": self._cache_evictions,
            "hit_rate": hit_rate,
        }


# ============================================================
# Convenience Functions
# ============================================================

_detector: Optional[LanguageDetector] = None


def get_detector() -> LanguageDetector:
    """Get a singleton instance of the language detector."""
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    return _detector


def detect_language(text: str) -> LanguageCode:
    """Convenience function to detect language."""
    return get_detector().detect(text)


def is_english(text: str) -> bool:
    """Convenience function to check if text is English."""
    return get_detector().is_english(text)


def detect_language_with_confidence(text: str) -> Tuple[LanguageCode, float]:
    """Convenience function to detect language with confidence."""
    return get_detector().detect_with_confidence(text)


def clear_language_cache() -> None:
    """Clear the language detection cache."""
    get_detector().clear_cache()


def get_language_cache_stats() -> dict[str, int | float]:
    """Get language detection cache statistics."""
    return get_detector().get_cache_stats()


# ============================================================
# Export
# ============================================================

__all__ = [
    "LanguageDetector",
    "get_detector",
    "detect_language",
    "is_english",
    "detect_language_with_confidence",
    "clear_language_cache",
    "get_language_cache_stats",
    "clean_text_for_detection",  # Added for testing/debugging
]