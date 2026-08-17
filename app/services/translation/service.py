"""Translation service - orchestrates translation providers.

This module provides the main translation service that:
- Manages translation providers
- Handles provider lifecycle (creation, caching, cleanup)
- Provides a clean API for translation operations
- Supports caching of translations (optional)
- Tracks metrics and health

The service follows the dependency injection pattern and
uses the TranslationProvider protocol for flexibility.

Example:
    service = TranslationService(
        provider=create_translation_provider(config),
        cache=TranslationCache(),
    )
    result = await service.translate(
        text="Hello, world!",
        source_language="en",
        target_language="fr",
    )
    print(result.text)  # "Bonjour, le monde !"
"""

import asyncio
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Any, Union

from app.services.translation.interface import (
    TranslationProviderType,
    TranslationResult,
    HealthCheckResult,
    TranslationConfig,
    TranslationError,
    TranslationProvider,
)
from app.services.translation.providers import create_translation_provider
from config.settings import settings

logger = logging.getLogger(__name__)


# ============================================================
# Cache Statistics
# ============================================================

@dataclass(slots=True)
class CacheStatistics:
    """Statistics for the translation cache."""
    
    size: int = 0
    max_size: int = 0
    hits: int = 0
    misses: int = 0
    ttl_seconds: Optional[int] = None
    
    @property
    def hit_rate(self) -> float:
        """Calculate the cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def used_percent(self) -> float:
        """Calculate the cache usage percentage."""
        return (self.size / self.max_size * 100) if self.max_size > 0 else 0.0


# ============================================================
# Translation Cache
# ============================================================

@dataclass(slots=True)
class TranslationCache:
    """LRU cache for translation results using OrderedDict."""
    
    max_size: int = 1000
    ttl_seconds: Optional[int] = None  # None = no expiration
    
    _cache: OrderedDict[Tuple[str, str, str], Tuple[TranslationResult, float]] = field(
        default_factory=OrderedDict
    )
    _hits: int = 0
    _misses: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    
    def _get_key(self, text: str, source: str, target: str) -> Tuple[str, str, str]:
        """Get cache key from text and languages."""
        return (text, source, target)
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry is expired."""
        if self.ttl_seconds is None:
            return False
        return (datetime.utcnow().timestamp() - timestamp) > self.ttl_seconds
    
    async def get(self, text: str, source: str, target: str) -> Optional[TranslationResult]:
        """Get a translation from cache (thread-safe)."""
        async with self._lock:
            key = self._get_key(text, source, target)
            
            if key not in self._cache:
                self._misses += 1
                return None
            
            result, timestamp = self._cache[key]
            
            # Check TTL
            if self._is_expired(timestamp):
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used) - true LRU
            self._cache.move_to_end(key)
            self._hits += 1
            return result
    
    async def set(self, text: str, source: str, target: str, result: TranslationResult) -> None:
        """Store a translation in cache (thread-safe)."""
        async with self._lock:
            key = self._get_key(text, source, target)
            
            # Evict oldest if cache is full (true LRU)
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = (result, datetime.utcnow().timestamp())
    
    async def clear(self) -> None:
        """Clear the cache (thread-safe)."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    async def get_stats(self) -> CacheStatistics:
        """Get cache statistics (thread-safe)."""
        async with self._lock:
            return CacheStatistics(
                size=len(self._cache),
                max_size=self.max_size,
                hits=self._hits,
                misses=self._misses,
                ttl_seconds=self.ttl_seconds,
            )


# ============================================================
# Metrics Snapshot
# ============================================================

@dataclass(slots=True)
class MetricsSnapshot:
    """Snapshot of translation metrics."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0.0
    total_characters: int = 0
    provider: str = ""
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate."""
        total = self.total_requests
        return (self.successful_requests / total * 100) if total > 0 else 0.0
    
    @property
    def avg_duration_ms(self) -> float:
        """Calculate the average duration."""
        total = self.total_requests
        return (self.total_duration_ms / total) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "total_duration_ms": self.total_duration_ms,
            "total_characters": self.total_characters,
            "provider": self.provider,
        }


# ============================================================
# Translation Metrics
# ============================================================

@dataclass(slots=True)
class TranslationMetrics:
    """Metrics for translation operations (thread-safe)."""
    
    _total_requests: int = 0
    _successful_requests: int = 0
    _failed_requests: int = 0
    _total_duration_ms: float = 0.0
    _total_characters: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    _provider: TranslationProviderType = TranslationProviderType.GOOGLE
    
    async def record(
        self,
        duration_ms: float,
        success: bool,
        char_count: int = 0,
    ) -> None:
        """Record a translation request (thread-safe)."""
        async with self._lock:
            self._total_requests += 1
            self._total_duration_ms += duration_ms
            self._total_characters += char_count
            
            if success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1
    
    async def snapshot(self, provider: TranslationProviderType) -> MetricsSnapshot:
        """Get a snapshot of metrics (thread-safe)."""
        async with self._lock:
            return MetricsSnapshot(
                total_requests=self._total_requests,
                successful_requests=self._successful_requests,
                failed_requests=self._failed_requests,
                total_duration_ms=self._total_duration_ms,
                total_characters=self._total_characters,
                provider=provider.value,
            )


# ============================================================
# Service Statistics
# ============================================================

@dataclass(slots=True)
class ServiceStatistics:
    """Comprehensive service statistics."""
    
    provider: str
    started_at: str
    uptime_seconds: float
    closed: bool
    cache: CacheStatistics
    metrics: MetricsSnapshot


# ============================================================
# Translation Service
# ============================================================

class TranslationService:
    """
    Translation service that orchestrates translation providers.
    
    Features:
    - Provider lifecycle management
    - Optional caching of translations
    - Health checks
    - Metrics tracking
    - Graceful fallback on failure
    
    The service is designed with dependency injection for testability.
    
    Example:
        from app.services.translation import create_translation_provider
        
        provider = create_translation_provider(config)
        cache = TranslationCache(max_size=1000)
        metrics = TranslationMetrics()
        
        service = TranslationService(
            provider=provider,
            cache=cache,
            metrics=metrics,
        )
        
        result = await service.translate(
            text="Hello, world!",
            source_language="en",
            target_language="fr",
        )
    """

    def __init__(
        self,
        provider: TranslationProvider,
        cache: Optional[TranslationCache] = None,
        metrics: Optional[TranslationMetrics] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ):
        """
        Initialize the translation service.
        
        Args:
            provider: The translation provider to use
            cache: Optional cache for translations
            metrics: Optional metrics tracker
            clock: Optional clock function for time (for testing)
        """
        self._provider = provider
        self._cache = cache
        self._metrics = metrics or TranslationMetrics()
        self._clock = clock or datetime.utcnow
        
        # Service state
        self._closed = False
        self._started_at = self._clock()
        self._lock = asyncio.Lock()
        
        logger.info(
            "TranslationService initialized: provider=%s, cache=%s",
            provider.provider_type,
            cache is not None,
        )

    @classmethod
    def create_default(
        cls,
        config: Optional[TranslationConfig] = None,
        enable_cache: bool = True,
        cache_max_size: int = 1000,
        cache_ttl: Optional[int] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> "TranslationService":
        """
        Create a default translation service with standard components.
        
        Args:
            config: Translation configuration
            enable_cache: Whether to enable caching
            cache_max_size: Maximum cache size
            cache_ttl: Cache TTL in seconds
            clock: Optional clock function for time (for testing)
            
        Returns:
            TranslationService: Configured service
        """
        if config is None:
            config = cls._load_config_from_settings()
        
        provider = create_translation_provider(config)
        cache = TranslationCache(
            max_size=cache_max_size if enable_cache else 0,
            ttl_seconds=cache_ttl,
        ) if enable_cache else None
        
        return cls(
            provider=provider,
            cache=cache,
            metrics=TranslationMetrics(),
            clock=clock,
        )
    
    @staticmethod
    def _load_config_from_settings() -> TranslationConfig:
        """Load translation configuration from settings."""
        provider_str = getattr(settings, 'translation_provider', 'google')
        
        try:
            provider = TranslationProviderType(provider_str)
        except ValueError:
            logger.warning(
                "Unknown translation provider '%s', using Google",
                provider_str,
            )
            provider = TranslationProviderType.GOOGLE
        
        return TranslationConfig(
            provider=provider,
            timeout=getattr(settings, 'translation_timeout', 15),
            retry_count=getattr(settings, 'translation_retry_count', 3),
            retry_delay=getattr(settings, 'translation_retry_delay', 1.0),
            retry_backoff_factor=getattr(settings, 'translation_retry_backoff', 2.0),
            deepl_api_key=getattr(settings, 'deepl_api_key', None),
            azure_translator_key=getattr(settings, 'azure_translator_key', None),
            azure_translator_endpoint=getattr(settings, 'azure_translator_endpoint', None),
            azure_translator_region=getattr(settings, 'azure_translator_region', None),
            google_cloud_project=getattr(settings, 'google_cloud_project', None),
            google_application_credentials=getattr(
                settings, 'google_application_credentials', None
            ),
        )

    @property
    def provider_type(self) -> TranslationProviderType:
        """Get the provider type."""
        return self._provider.provider_type

    async def _record_metrics(
        self,
        duration_ms: float,
        success: bool,
        char_count: int = 0,
    ) -> None:
        """Record metrics (thread-safe)."""
        await self._metrics.record(duration_ms, success, char_count)

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = "en",
        use_cache: bool = True,
    ) -> TranslationResult:
        """
        Translate a single text.
        
        Args:
            text: The text to translate
            source_language: ISO 639-1 code of the source language
            target_language: ISO 639-1 code of the target language (default: 'en')
            use_cache: Whether to use the cache
            
        Returns:
            TranslationResult: The translation result
            
        Raises:
            TranslationError: If translation fails
        """
        if self._closed:
            raise TranslationError("Translation service is closed")
        
        if not text or not text.strip():
            return TranslationResult(
                text=text,
                source_language=source_language,
                target_language=target_language,
                success=True,
            )

        start_time = self._clock().timestamp()

        # Check cache
        if use_cache and self._cache is not None:
            cached = await self._cache.get(text, source_language, target_language)
            if cached is not None:
                logger.debug("Cache hit for text: %s...", text[:50])
                return cached

        try:
            result = await self._provider.translate(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
            
            # Cache the result
            if use_cache and self._cache is not None:
                await self._cache.set(text, source_language, target_language, result)
            
            # Record metrics
            duration_ms = (self._clock().timestamp() - start_time) * 1000
            await self._record_metrics(duration_ms, result.success, len(text))
            
            logger.debug(
                "Translation completed: %s -> %s, duration=%.2fms",
                source_language,
                target_language,
                duration_ms,
            )
            
            return result

        except Exception as e:
            duration_ms = (self._clock().timestamp() - start_time) * 1000
            await self._record_metrics(duration_ms, False, len(text))
            logger.error(
                "Translation failed: %s -> %s, error: %s",
                source_language,
                target_language,
                e,
            )
            
            # Return a fallback result
            return TranslationResult(
                text=text,
                source_language=source_language,
                target_language=target_language,
                error=e,
                success=False,
            )

    async def translate_many(
        self,
        texts: List[str],
        source_language: str,
        target_language: str = "en",
        use_cache: bool = True,
    ) -> List[TranslationResult]:
        """
        Translate multiple texts.
        
        Args:
            texts: The texts to translate
            source_language: ISO 639-1 code of the source language
            target_language: ISO 639-1 code of the target language (default: 'en')
            use_cache: Whether to use the cache
            
        Returns:
            List[TranslationResult]: The translation results
        """
        if self._closed:
            raise TranslationError("Translation service is closed")
        
        if not texts:
            return []

        start_time = self._clock().timestamp()
        results: List[Optional[TranslationResult]] = []
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        # Check cache for each text
        for i, text in enumerate(texts):
            if not text or not text.strip():
                results.append(TranslationResult(
                    text=text,
                    source_language=source_language,
                    target_language=target_language,
                    success=True,
                ))
                continue

            if use_cache and self._cache is not None:
                cached = await self._cache.get(text, source_language, target_language)
                if cached is not None:
                    results.append(cached)
                    continue

            # Not in cache, mark for translation
            uncached_indices.append(i)
            uncached_texts.append(text)
            results.append(None)

        # Translate uncached texts
        if uncached_texts:
            try:
                translated = await self._provider.translate_many(
                    texts=uncached_texts,
                    source_language=source_language,
                    target_language=target_language,
                )

                # Store results in the correct positions
                for idx, result in zip(uncached_indices, translated):
                    results[idx] = result
                    if use_cache and self._cache is not None:
                        await self._cache.set(
                            uncached_texts[uncached_indices.index(idx)],
                            source_language,
                            target_language,
                            result,
                        )

            except Exception as e:
                logger.error(
                    "Batch translation failed: %s -> %s, error: %s",
                    source_language,
                    target_language,
                    e,
                )
                # Fill any remaining None results with fallback
                for i in range(len(results)):
                    if results[i] is None:
                        results[i] = TranslationResult(
                            text=texts[i] if i < len(texts) else "",
                            source_language=source_language,
                            target_language=target_language,
                            error=e,
                            success=False,
                        )

        # Record metrics
        duration_ms = (self._clock().timestamp() - start_time) * 1000
        success_count = sum(1 for r in results if r and r.success)
        total_chars = sum(len(t) for t in texts)
        await self._record_metrics(duration_ms, success_count == len(results), total_chars)

        # Type-safe return
        return [r for r in results if r is not None]  # type: ignore

    async def health_check(self) -> HealthCheckResult:
        """
        Check the health of the translation service.
        
        Returns:
            HealthCheckResult: The health check result
        """
        if self._closed:
            return HealthCheckResult(
                healthy=False,
                provider=self.provider_type,
                message="Translation service is closed",
                checked_at=self._clock().isoformat(),
            )
        
        try:
            result = await self._provider.health_check()
            
            # Add service-level information
            return HealthCheckResult(
                healthy=result.healthy,
                latency_ms=result.latency_ms,
                provider=result.provider,
                message=result.message,
                details={
                    **(result.details or {}),
                    "service_metrics": (await self.get_metrics()).to_dict(),
                },
                checked_at=self._clock().isoformat(),
            )
        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                provider=self.provider_type,
                message=f"Health check failed: {e}",
                checked_at=self._clock().isoformat(),
            )

    async def get_metrics(self) -> MetricsSnapshot:
        """Get service metrics snapshot."""
        return await self._metrics.snapshot(self.provider_type)

    async def get_cache_stats(self) -> CacheStatistics:
        """Get cache statistics."""
        if self._cache is None:
            return CacheStatistics(max_size=0)
        return await self._cache.get_stats()

    async def get_service_stats(self) -> ServiceStatistics:
        """Get comprehensive service statistics."""
        cache_stats = await self.get_cache_stats()
        metrics_snapshot = await self.get_metrics()
        
        return ServiceStatistics(
            provider=self.provider_type.value,
            started_at=self._started_at.isoformat(),
            uptime_seconds=(self._clock() - self._started_at).total_seconds(),
            closed=self._closed,
            cache=cache_stats,
            metrics=metrics_snapshot,
        )

    async def close(self) -> None:
        """Close the translation service and release resources."""
        if not self._closed:
            await self._provider.close()
            self._closed = True
            logger.info("Translation service closed")
        
        if self._cache is not None:
            await self._cache.clear()

    async def clear_cache(self) -> None:
        """Clear the translation cache."""
        if self._cache is not None:
            await self._cache.clear()
            logger.info("Translation cache cleared")

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()


# ============================================================
# Singleton Instance
# ============================================================

_service: Optional[TranslationService] = None
_service_lock = asyncio.Lock()


async def get_translation_service(
    config: Optional[TranslationConfig] = None,
    enable_cache: bool = True,
    cache_max_size: int = 1000,
    cache_ttl: Optional[int] = None,
) -> TranslationService:
    """
    Get a singleton instance of the translation service.
    
    Args:
        config: Translation configuration
        enable_cache: Whether to enable caching
        cache_max_size: Maximum cache size
        cache_ttl: Cache TTL in seconds
        
    Returns:
        TranslationService: The translation service
    """
    global _service
    
    if _service is None:
        async with _service_lock:
            if _service is None:
                if config is None:
                    config = TranslationService._load_config_from_settings()
                _service = TranslationService.create_default(
                    config=config,
                    enable_cache=enable_cache,
                    cache_max_size=cache_max_size,
                    cache_ttl=cache_ttl,
                )
    
    return _service


# ============================================================
# Convenience Functions
# ============================================================

async def translate_text(
    text: str,
    source_language: str,
    target_language: str = "en",
) -> TranslationResult:
    """Convenience function to translate a single text."""
    service = await get_translation_service()
    return await service.translate(text, source_language, target_language)


async def translate_texts(
    texts: List[str],
    source_language: str,
    target_language: str = "en",
) -> List[TranslationResult]:
    """Convenience function to translate multiple texts."""
    service = await get_translation_service()
    return await service.translate_many(texts, source_language, target_language)


# ============================================================
# Export
# ============================================================

__all__ = [
    "CacheStatistics",
    "TranslationCache",
    "MetricsSnapshot",
    "TranslationMetrics",
    "ServiceStatistics",
    "TranslationService",
    "get_translation_service",
    "translate_text",
    "translate_texts",
]