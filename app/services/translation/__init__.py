"""Translation service package.

This package provides a complete translation subsystem with:
- Provider abstraction (Protocol-based)
- Multiple provider implementations (Google, DeepL, Mock)
- Caching (LRU with TTL support)
- Metrics and observability
- Health checks
- Batch translation
- Thread-safe operations

The package is designed with dependency injection and follows
the Dependency Inversion Principle.

Public API:
    Primary entry points:
        - TranslationService: Main service orchestrator
        - get_translation_service: Singleton instance access
        - translate_text: Convenience function for single translation
        - translate_texts: Convenience function for batch translation

    Advanced/Internal:
        - TranslationProvider: Protocol for providers
        - TranslationProviderType: Enum of supported providers
        - TranslationConfig: Configuration dataclass
        - TranslationResult: Rich translation result
        - HealthCheckResult: Health check result
        
        - create_translation_provider: Factory for providers
        - TranslationCache: LRU cache for translations
        - TranslationMetrics: Metrics tracker

    Provider implementations (not typically imported directly):
        - GoogleTranslateProvider: Development/demo (unofficial API)
        - DeepLProvider: Production-ready
        - MockTranslationProvider: Testing

Examples:
    # Simple translation
    from app.services.translation import translate_text
    
    result = await translate_text(
        text="Hello, world!",
        source_language="en",
        target_language="fr",
    )
    print(result.text)

    # Advanced usage with custom config
    from app.services.translation import (
        TranslationService,
        TranslationConfig,
        TranslationProviderType,
    )
    
    config = TranslationConfig(
        provider=TranslationProviderType.DEEPL,
        deepl_api_key="your-api-key",
    )
    service = TranslationService.create_default(config=config)
    result = await service.translate("Hello", "en", "fr")
"""

# ============================================================
# Version & Metadata
# ============================================================

__version__ = "1.0.0"
__author__ = "James Mwangi"
__license__ = "MIT"


# ============================================================
# Core Types (from interface.py)
# ============================================================

from app.services.translation.interface import (
    # Types
    LanguageCode,
    DEFAULT_LANGUAGE,
    TranslationProviderType,
    TranslationResult,
    HealthCheckResult,
    TranslationConfig,
    # Protocol
    TranslationProvider,
    # Exceptions
    TranslationError,
    TranslationTimeoutError,
    TranslationProviderError,
    TranslationRateLimitError,
)


# ============================================================
# Providers (from providers.py)
# ============================================================

from app.services.translation.providers import (
    # Base
    RetryPolicy,
    CircuitBreaker,
    BaseTranslationProvider,
    # Provider implementations
    GoogleTranslateProvider,
    DeepLProvider,
    MockTranslationProvider,
    # Factory
    create_translation_provider,
)


# ============================================================
# Service (from service.py)
# ============================================================

from app.services.translation.service import (
    # Cache
    CacheStatistics,
    TranslationCache,
    # Metrics
    MetricsSnapshot,
    TranslationMetrics,
    # Statistics
    ServiceStatistics,
    # Service
    TranslationService,
    # Singleton
    get_translation_service,
    # Convenience functions
    translate_text,
    translate_texts,
)


# ============================================================
# __all__ - Public API (Alphabetized)
# ============================================================

__all__ = [
    # === Core Types ===
    "DEFAULT_LANGUAGE",
    "HealthCheckResult",
    "LanguageCode",
    "TranslationConfig",
    "TranslationProviderType",
    "TranslationResult",
    
    # === Exceptions ===
    "TranslationError",
    "TranslationTimeoutError",
    "TranslationProviderError",
    "TranslationRateLimitError",
    
    # === Protocols ===
    "TranslationProvider",
    
    # === Provider Implementations ===
    "GoogleTranslateProvider",
    "DeepLProvider",
    "MockTranslationProvider",
    "BaseTranslationProvider",
    "RetryPolicy",
    "CircuitBreaker",
    
    # === Factory ===
    "create_translation_provider",
    
    # === Service ===
    "TranslationService",
    "get_translation_service",
    "translate_text",
    "translate_texts",
    
    # === Cache ===
    "TranslationCache",
    "CacheStatistics",
    
    # === Metrics ===
    "TranslationMetrics",
    "MetricsSnapshot",
    
    # === Statistics ===
    "ServiceStatistics",
]