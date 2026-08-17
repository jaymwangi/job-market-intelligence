"""Translation provider interface.

This module defines the interface for translation providers and the
supported provider types. The interface follows the dependency inversion
principle, allowing the translation service to work with any provider
that implements the TranslationProvider protocol.

Design decisions:
- Uses Protocol for duck typing (runtime and static checking)
- StrEnum for type-safe provider selection
- Async methods for non-blocking translation
- TranslationResult for rich return data (detected language, duration, etc.)
- Batch translation support for efficiency
- Health check for provider validation
- Exponential backoff retry configuration
- Type-safe language handling using strings (ISO 639-1 codes)

Example:
    class DeepLProvider(TranslationProvider):
        async def translate(
            self,
            text: str,
            source_language: str,
        ) -> TranslationResult:
            # Implementation using DeepL API
            ...

    provider = DeepLProvider(api_key="...")
    result = await provider.translate("Hello", "en")
    print(result.text)         # "Bonjour"
    print(result.duration_ms)  # 123.4
    print(result.success)      # True
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

# Language type - ISO 639-1 codes as strings
# For type checking, this is a string; at runtime, we use strings
LanguageCode = str


class TranslationProviderType(StrEnum):
    """Supported translation provider types.

    These map to the implementations in providers.py:
        - GOOGLE: googletrans (development/demo only)
        - DEEPL: DeepL API (production-ready)
        - AZURE: Azure Translator (production-ready)
        - MOCK: Mock provider for testing
    """
    GOOGLE = "google"
    DEEPL = "deepl"
    AZURE = "azure"
    MOCK = "mock"


# Default language constant
DEFAULT_LANGUAGE = "en"


@dataclass(frozen=True, slots=True)
class TranslationResult:
    """
    Result of a translation operation.
    
    Attributes:
        text: The translated text
        detected_language: The language detected from the source text (if available)
        provider: The provider that performed the translation
        duration_ms: The duration of the translation in milliseconds
        character_count: Number of characters translated (None if not reported)
        source_language: The source language used for translation
        target_language: The target language used for translation
        error: Any error that occurred during translation (for partial failures)
        success: Whether the translation was successful
    """
    text: str
    detected_language: str | None = None
    provider: TranslationProviderType | None = None
    duration_ms: float | None = None
    character_count: int | None = None
    source_language: str | None = None
    target_language: str = DEFAULT_LANGUAGE
    error: Exception | None = None
    success: bool = True


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    """
    Result of a health check operation.
    
    Attributes:
        healthy: Whether the provider is healthy
        latency_ms: The latency of the health check in milliseconds
        provider: The provider type
        message: A human-readable message (for debugging)
        details: Additional provider-specific details
        checked_at: ISO timestamp of when the check was performed
    """
    healthy: bool
    latency_ms: float | None = None
    provider: TranslationProviderType | None = None
    message: str | None = None
    details: dict | None = None
    checked_at: str | None = None


@runtime_checkable
class TranslationProvider(Protocol):
    """
    Protocol for translation providers.
    
    Any class that implements this protocol can be used as a translation
    provider. This allows for easy swapping of translation backends
    without changing the rest of the application.
    
    Methods:
        translate: Translate text from source to target language
        translate_many: Translate multiple texts efficiently
        health_check: Check if the provider is operational
        close: Clean up provider resources
    
    Example:
        @dataclass
        class MyTranslationProvider:
            async def translate(
                self,
                text: str,
                source_language: str,
            ) -> TranslationResult:
                # Implementation here
                return TranslationResult(text=translated_text)
    """
    
    @property
    def provider_type(self) -> TranslationProviderType:
        """Get the provider type."""
        ...
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> TranslationResult:
        """
        Translate text from source language to target language.
        
        Args:
            text: The text to translate
            source_language: ISO 639-1 code of the source language
            target_language: ISO 639-1 code of the target language (default: 'en')
            
        Returns:
            TranslationResult: The translation result
            
        Raises:
            TranslationError: If translation fails
            TranslationTimeoutError: If the translation times out
            TranslationRateLimitError: If rate limit is exceeded
            TranslationProviderError: If a provider-specific error occurs
        """
        ...
    
    async def translate_many(
        self,
        texts: list[str],
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> list[TranslationResult]:
        """
        Translate multiple texts efficiently.
        
        This method should be implemented by providers that support
        batch translation. Fallback implementation can call translate()
        sequentially.
        
        Important:
            The result list will be in the same order as the input texts.
            If an individual translation fails, the result will contain
            the error field set to the exception. The method itself will
            not raise an exception for individual failures.
        
        Args:
            texts: The texts to translate
            source_language: ISO 639-1 code of the source language
            target_language: ISO 639-1 code of the target language (default: 'en')
            
        Returns:
            list[TranslationResult]: The translation results in the same order
            
        Raises:
            TranslationError: If a critical error occurs (not per-item)
            TranslationTimeoutError: If the batch request times out
            TranslationRateLimitError: If rate limit is exceeded
            TranslationProviderError: If a provider-specific error occurs
        """
        ...
    
    async def health_check(self) -> HealthCheckResult:
        """
        Check if the provider is operational.
        
        This method should perform a lightweight check to verify that
        the provider can accept translation requests.
        
        Returns:
            HealthCheckResult: The health check result
        """
        ...
    
    async def close(self) -> None:
        """
        Clean up provider resources.
        
        This method should be called when the provider is no longer needed
        to close connections and release resources.
        """
        ...


# ============================================================
# Exceptions
# ============================================================

class TranslationError(Exception):
    """Base exception for translation errors."""
    pass


class TranslationTimeoutError(TranslationError):
    """Raised when a translation request times out."""
    pass


class TranslationProviderError(TranslationError):
    """
    Raised when a provider-specific error occurs.
    
    Attributes:
        provider: The provider type that raised the error
        status_code: The HTTP status code (if applicable)
        retry_after: Seconds to wait before retrying (if applicable)
    """
    def __init__(
        self,
        message: str,
        provider: TranslationProviderType | None = None,
        status_code: int | None = None,
        retry_after: int | None = None,
    ):
        self.provider = provider
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(message)


class TranslationRateLimitError(TranslationError):
    """
    Raised when rate limit is exceeded.
    
    Attributes:
        provider: The provider type that raised the error
        retry_after: Seconds to wait before retrying
        limit: The rate limit that was exceeded
    """
    def __init__(
        self,
        message: str,
        provider: TranslationProviderType | None = None,
        retry_after: int | None = None,
        limit: int | None = None,
    ):
        self.provider = provider
        self.retry_after = retry_after
        self.limit = limit
        super().__init__(message)


# ============================================================
# Configuration
# ============================================================

@dataclass(frozen=True, slots=True)
class TranslationConfig:
    """Configuration for translation providers."""
    
    provider: TranslationProviderType = TranslationProviderType.GOOGLE
    timeout: int = 15
    retry_count: int = 3
    retry_delay: float = 1.0
    retry_backoff_factor: float = 2.0  # Exponential backoff multiplier
    retry_jitter: float = 0.1  # Random jitter to prevent thundering herd
    
    # Provider-specific configurations
    deepl_api_key: str | None = None
    azure_translator_key: str | None = None
    azure_translator_endpoint: str | None = None
    azure_translator_region: str | None = None
    google_cloud_project: str | None = None
    google_application_credentials: str | None = None
    
    # Batch settings
    batch_max_size: int = 50
    
    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be greater than 0")
        if self.retry_backoff_factor < 1.0:
            raise ValueError("retry_backoff_factor must be >= 1.0")
        if not (0 <= self.retry_jitter <= 1.0):
            raise ValueError("retry_jitter must be between 0 and 1.0")
        if self.batch_max_size <= 0:
            raise ValueError("batch_max_size must be greater than 0")


# ============================================================
# Export
# ============================================================

__all__ = [
    "LanguageCode",
    "DEFAULT_LANGUAGE",
    "TranslationProviderType",
    "TranslationResult",
    "HealthCheckResult",
    "TranslationProvider",
    "TranslationConfig",
    "TranslationError",
    "TranslationTimeoutError",
    "TranslationProviderError",
    "TranslationRateLimitError",
]