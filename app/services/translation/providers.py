"""Translation provider implementations.

This module provides concrete implementations of the TranslationProvider
protocol for various translation services:

- GoogleTranslateProvider: Uses googletrans (development/demo only)
- DeepLProvider: Uses DeepL API (production-ready)
- MockTranslationProvider: Mock provider for testing

All providers implement the TranslationProvider protocol from interface.py
and support async translation, batch translation, health checks, and
resource cleanup.

Design decisions:
- Tenacity for retry logic with exponential backoff
- Session reuse for HTTP clients (performance)
- Health checks for provider validation
- Circuit breaker for resilience
- Metrics for observability
- Context manager support for resource cleanup
- Graceful fallback to original text on failure
- Structured logging for debugging
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Protocol, runtime_checkable

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random,
    retry_if_exception_type,
    before_sleep_log,
)

from app.services.translation.interface import (
    TranslationProviderType,
    TranslationResult,
    HealthCheckResult,
    TranslationProvider,
    TranslationError,
    TranslationTimeoutError,
    TranslationProviderError,
    TranslationRateLimitError,
    TranslationConfig,
    DEFAULT_LANGUAGE,
)

logger = logging.getLogger(__name__)


# ============================================================
# Retry Policy
# ============================================================

@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Retry policy for translation providers."""
    
    attempts: int = 3
    initial_delay: float = 1.0
    backoff: float = 2.0
    jitter: float = 0.1
    
    def __post_init__(self) -> None:
        """Validate retry policy values."""
        if self.attempts < 0:
            raise ValueError("attempts must be non-negative")
        if self.initial_delay <= 0:
            raise ValueError("initial_delay must be greater than 0")
        if self.backoff < 1.0:
            raise ValueError("backoff must be >= 1.0")
        if not (0 <= self.jitter <= 1.0):
            raise ValueError("jitter must be between 0 and 1.0")


# ============================================================
# Circuit Breaker
# ============================================================

@dataclass
class CircuitBreaker:
    """Circuit breaker for provider resilience."""
    
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_attempts: int = 3
    
    _failures: int = 0
    _state: str = "closed"  # closed, open, half_open
    _last_failure_time: float = 0.0
    _half_open_attempts: int = 0
    
    def record_failure(self) -> None:
        """Record a failure."""
        self._failures += 1
        self._last_failure_time = time.time()
        
        if self._failures >= self.failure_threshold:
            self._state = "open"
            logger.warning("Circuit breaker opened after %d failures", self._failures)
    
    def record_success(self) -> None:
        """Record a success."""
        if self._state == "half_open":
            self._half_open_attempts += 1
            if self._half_open_attempts >= self.half_open_max_attempts:
                self._state = "closed"
                self._failures = 0
                self._half_open_attempts = 0
                logger.info("Circuit breaker closed after successful attempts")
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        if self._state == "closed":
            return True
        
        if self._state == "open":
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = "half_open"
                self._half_open_attempts = 0
                logger.info("Circuit breaker transitioning to half-open")
                return True
            return False
        
        # half_open - allow limited requests
        return self._half_open_attempts < self.half_open_max_attempts
    
    @property
    def is_open(self) -> bool:
        return self._state == "open"
    
    @property
    def is_half_open(self) -> bool:
        return self._state == "half_open"
    
    def reset(self) -> None:
        """Reset the circuit breaker."""
        self._failures = 0
        self._state = "closed"
        self._last_failure_time = 0.0
        self._half_open_attempts = 0


# ============================================================
# Base Provider
# ============================================================

class BaseTranslationProvider:
    """Base provider with common functionality."""

    def __init__(self, config: TranslationConfig):
        self.config = config
        self._provider_type: TranslationProviderType
        self._session: Optional[aiohttp.ClientSession] = None
        self._closed = False
        self._circuit_breaker = CircuitBreaker()
        self._metrics: Dict[str, Any] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "timeout_calls": 0,
            "total_duration_ms": 0.0,
            "total_characters": 0,
            "started_at": datetime.utcnow().isoformat(),
        }

    @property
    def provider_type(self) -> TranslationProviderType:
        return self._provider_type

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a reusable HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._closed = True
            logger.debug("Provider session closed: %s", self._provider_type)

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()

    async def _health_check_request(self) -> HealthCheckResult:
        """Perform a health check request."""
        raise NotImplementedError

    async def health_check(self) -> HealthCheckResult:
        """Check provider health."""
        if self._closed:
            return HealthCheckResult(
                healthy=False,
                provider=self._provider_type,
                message="Provider is closed",
                checked_at=datetime.utcnow().isoformat(),
            )

        try:
            result = await self._health_check_request()
            return HealthCheckResult(
                healthy=result.healthy,
                latency_ms=result.latency_ms,
                provider=self._provider_type,
                message=result.message,
                details=result.details,
                checked_at=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                provider=self._provider_type,
                message=str(e),
                checked_at=datetime.utcnow().isoformat(),
            )

    def _create_result(
        self,
        text: str,
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
        detected_language: Optional[str] = None,
        duration_ms: Optional[float] = None,
        char_count: Optional[int] = None,
        error: Optional[Exception] = None,
    ) -> TranslationResult:
        """Create a translation result with consistent metadata."""
        return TranslationResult(
            text=text,
            detected_language=detected_language,
            provider=self._provider_type,
            duration_ms=duration_ms,
            character_count=char_count,
            source_language=source_language,
            target_language=target_language,
            error=error,
            success=error is None,
        )

    def _record_metrics(self, duration_ms: float, char_count: int, success: bool) -> None:
        """Record metrics for the provider."""
        self._metrics["total_calls"] += 1
        self._metrics["total_duration_ms"] += duration_ms
        self._metrics["total_characters"] += char_count
        
        if success:
            self._metrics["successful_calls"] += 1
        else:
            self._metrics["failed_calls"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics."""
        total_calls = self._metrics["total_calls"]
        return {
            **self._metrics,
            "avg_duration_ms": (
                self._metrics["total_duration_ms"] / total_calls if total_calls > 0 else 0
            ),
            "success_rate": (
                self._metrics["successful_calls"] / total_calls * 100 if total_calls > 0 else 0
            ),
            "circuit_breaker_state": self._circuit_breaker._state,
            "circuit_breaker_failures": self._circuit_breaker._failures,
        }
# ============================================================
# Google Translate Provider (Development/Demo)
# ============================================================

# Import googletrans with fallback
try:
    from googletrans import Translator  # type: ignore
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False
    Translator = None  # type: ignore


class GoogleTranslateProvider(BaseTranslationProvider):
    """
    Google Translate provider using googletrans.
    
    WARNING: This provider is for development and demonstration only.
    It uses an unofficial API and may break without notice.
    For production, use DeepLProvider or AzureTranslatorProvider.
    """

    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self._provider_type = TranslationProviderType.GOOGLE
        self._translator: Any = None
        logger.warning(
            "GoogleTranslateProvider is using an unofficial API. "
            "For production, use DeepLProvider or AzureTranslatorProvider."
        )

    def _get_translator(self) -> Any:
        """Lazy import of googletrans."""
        if self._translator is None:
            # Try importing again in case it was installed after module load
            if not HAS_GOOGLETRANS:
                try:
                    from googletrans import Translator as _Translator  # type: ignore
                    self._translator = _Translator()
                    return self._translator
                except ImportError:
                    raise TranslationProviderError(
                        "googletrans is not installed. "
                        "Install it with: pip install googletrans==4.0.2",
                        provider=self._provider_type,
                    )
            # HAS_GOOGLETRANS is True, but the type checker doesn't know that
            self._translator = Translator()  # type: ignore
        return self._translator

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10) + wait_random(0, 0.5),
        retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> TranslationResult:
        """Translate using googletrans (async)."""
        if not text or not text.strip():
            return self._create_result(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )

        start_time = time.perf_counter()

        try:
            translator = self._get_translator()

            # googletrans 4.0.2 is async - await directly
            if source_language and source_language != DEFAULT_LANGUAGE:
                result = await translator.translate(
                    text,
                    dest=target_language,
                    src=source_language,
                )
            else:
                result = await translator.translate(
                    text,
                    dest=target_language,
                )

            duration_ms = (time.perf_counter() - start_time) * 1000
            char_count = len(text)

            translation_result = self._create_result(
                text=result.text,
                source_language=source_language,
                target_language=target_language,
                detected_language=getattr(result, "src", source_language),
                duration_ms=duration_ms,
                char_count=char_count,
            )

            self._record_metrics(duration_ms, char_count, True)
            return translation_result

        except asyncio.TimeoutError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._record_metrics(duration_ms, len(text), False)
            raise TranslationTimeoutError(f"Google Translate timeout: {e}") from e
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._record_metrics(duration_ms, len(text), False)
            logger.warning("Google Translate failed: %s, returning original text", e)
            return self._create_result(
                text=text,
                source_language=source_language,
                target_language=target_language,
                duration_ms=duration_ms,
                char_count=len(text),
                error=e,
            )

    async def translate_many(
        self,
        texts: List[str],
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> List[TranslationResult]:
        """Translate multiple texts sequentially."""
        results = []
        for text in texts:
            results.append(await self.translate(text, source_language, target_language))
        return results

    async def _health_check_request(self) -> HealthCheckResult:
        """Health check for Google Translate."""
        start_time = time.perf_counter()
        try:
            result = await self.translate("hello", "en", "fr")
            latency_ms = (time.perf_counter() - start_time) * 1000
            return HealthCheckResult(
                healthy=result.success,
                latency_ms=latency_ms,
                provider=self._provider_type,
                message="OK" if result.success else "Translation failed",
                checked_at=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                provider=self._provider_type,
                message=str(e),
                checked_at=datetime.utcnow().isoformat(),
            )

# ============================================================
# DeepL Provider (Production-Ready)
# ============================================================

class DeepLProvider(BaseTranslationProvider):
    """
    DeepL API provider - Production-ready.
    
    Requires DEEPL_API_KEY environment variable or config.
    Supports:
    - High-quality translations
    - Batch translation
    - Language detection
    - Formality control (optional)
    """

    def __init__(
        self,
        config: TranslationConfig,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepl.com/v2",
    ):
        super().__init__(config)
        self._provider_type = TranslationProviderType.DEEPL
        self.api_key = api_key or config.deepl_api_key
        self.base_url = base_url.rstrip("/")

        if not self.api_key:
            raise TranslationProviderError(
                "DeepL API key is required. "
                "Set DEEPL_API_KEY in environment or config.",
                provider=self._provider_type,
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10) + wait_random(0, 0.5),
        retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> TranslationResult:
        """Translate using DeepL API."""
        if not text or not text.strip():
            return self._create_result(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )

        # Check circuit breaker
        if not self._circuit_breaker.allow_request():
            raise TranslationProviderError(
                "Circuit breaker is open",
                provider=self._provider_type,
            )

        start_time = time.perf_counter()
        session = await self._get_session()

        data = {
            "auth_key": self.api_key,
            "text": text,
            "target_lang": target_language.upper(),
        }

        if source_language and source_language != DEFAULT_LANGUAGE:
            data["source_lang"] = source_language.upper()

        try:
            async with session.post(
                f"{self.base_url}/translate",
                data=data,
            ) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    self._circuit_breaker.record_failure()
                    raise TranslationRateLimitError(
                        "DeepL rate limit exceeded",
                        provider=self._provider_type,
                        retry_after=retry_after,
                    )

                if response.status != 200:
                    error_body = await response.text()
                    self._circuit_breaker.record_failure()
                    raise TranslationProviderError(
                        f"DeepL API error {response.status}: {error_body}",
                        provider=self._provider_type,
                        status_code=response.status,
                    )

                result = await response.json()
                translation = result["translations"][0]

                duration_ms = (time.perf_counter() - start_time) * 1000
                char_count = len(text)

                self._circuit_breaker.record_success()
                self._record_metrics(duration_ms, char_count, True)

                return self._create_result(
                    text=translation["text"],
                    source_language=source_language,
                    target_language=target_language,
                    detected_language=translation.get("detected_source_language", source_language).lower(),
                    duration_ms=duration_ms,
                    char_count=char_count,
                )

        except asyncio.TimeoutError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._circuit_breaker.record_failure()
            self._record_metrics(duration_ms, len(text), False)
            raise TranslationTimeoutError(f"DeepL translation timeout: {e}") from e
        except TranslationRateLimitError:
            self._circuit_breaker.record_failure()
            raise
        except aiohttp.ClientError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._circuit_breaker.record_failure()
            self._record_metrics(duration_ms, len(text), False)
            raise TranslationProviderError(
                f"DeepL client error: {e}",
                provider=self._provider_type,
            ) from e
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._circuit_breaker.record_failure()
            self._record_metrics(duration_ms, len(text), False)
            logger.warning("DeepL translation failed: %s, returning original text", e)
            return self._create_result(
                text=text,
                source_language=source_language,
                target_language=target_language,
                duration_ms=duration_ms,
                char_count=len(text),
                error=e,
            )

    async def translate_many(
        self,
        texts: List[str],
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> List[TranslationResult]:
        """Translate multiple texts using DeepL batch API."""
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [self._create_result(text="", source_language=source_language, target_language=target_language) for _ in texts]

        # DeepL supports up to 50 texts per request
        batch_size = getattr(self.config, 'batch_max_size', 50)

        results = []
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            batch_results = await self._translate_batch(
                batch,
                source_language,
                target_language,
            )
            results.extend(batch_results)

        # Reconstruct original order
        ordered_results = []
        idx = 0
        for text in texts:
            if text and text.strip():
                ordered_results.append(results[idx])
                idx += 1
            else:
                ordered_results.append(
                    self._create_result(
                        text=text,
                        source_language=source_language,
                        target_language=target_language,
                    )
                )

        return ordered_results

    async def _translate_batch(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
    ) -> List[TranslationResult]:
        """Translate a batch of texts."""
        if not texts:
            return []

        session = await self._get_session()

        data = {
            "auth_key": self.api_key,
            "text": texts,
            "target_lang": target_language.upper(),
        }

        if source_language and source_language != DEFAULT_LANGUAGE:
            data["source_lang"] = source_language.upper()

        try:
            async with session.post(
                f"{self.base_url}/translate",
                data=data,
            ) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    raise TranslationRateLimitError(
                        "DeepL rate limit exceeded",
                        provider=self._provider_type,
                        retry_after=retry_after,
                    )

                if response.status != 200:
                    error_body = await response.text()
                    raise TranslationProviderError(
                        f"DeepL API error {response.status}: {error_body}",
                        provider=self._provider_type,
                        status_code=response.status,
                    )

                result = await response.json()
                translations = result["translations"]

                results = []
                for i, translation in enumerate(translations):
                    results.append(
                        TranslationResult(
                            text=translation["text"],
                            source_language=source_language,
                            target_language=target_language,
                            detected_language=translation.get(
                                "detected_source_language", source_language
                            ).lower(),
                            character_count=len(texts[i]),
                            provider=self._provider_type,
                            success=True,
                        )
                    )

                return results

        except Exception as e:
            logger.warning("DeepL batch translation failed: %s", e)
            # Fallback to individual translations
            results = []
            for text in texts:
                result = await self.translate(text, source_language, target_language)
                results.append(result)
            return results

    async def _health_check_request(self) -> HealthCheckResult:
        """Health check for DeepL."""
        start_time = time.perf_counter()
        try:
            result = await self.translate("Hello", "en", "fr")
            latency_ms = (time.perf_counter() - start_time) * 1000
            return HealthCheckResult(
                healthy=result.success,
                latency_ms=latency_ms,
                provider=self._provider_type,
                message="OK" if result.success else "Translation failed",
                checked_at=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                provider=self._provider_type,
                message=str(e),
                checked_at=datetime.utcnow().isoformat(),
            )


# ============================================================
# Mock Provider (Testing)
# ============================================================

class MockTranslationProvider(BaseTranslationProvider):
    """
    Mock translation provider for testing.
    
    Simulates translation by adding a prefix and tracking calls.
    Useful for:
    - Unit tests
    - Integration tests
    - Development without API keys
    """

    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self._provider_type = TranslationProviderType.MOCK
        self._call_count = 0
        self._batch_call_count = 0
        self._health_check_calls = 0
        self._simulate_failure = False
        self._failure_rate = 0.0

    def set_failure_rate(self, rate: float) -> None:
        """Set the failure rate for testing (0.0 - 1.0)."""
        self._failure_rate = max(0.0, min(1.0, rate))

    def set_simulate_failure(self, enabled: bool) -> None:
        """Enable or disable failure simulation."""
        self._simulate_failure = enabled

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> TranslationResult:
        """Mock translation with configurable behavior."""
        self._call_count += 1

        if self._simulate_failure or random.random() < self._failure_rate:
            self._record_metrics(0, len(text) if text else 0, False)
            raise TranslationProviderError(
                "Mock translation failure",
                provider=self._provider_type,
            )

        if not text or not text.strip():
            result = self._create_result(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
            self._record_metrics(0, len(text) if text else 0, True)
            return result

        # Simulate work
        await asyncio.sleep(0.01 * random.random())

        # Simple mock: add a prefix indicating source language
        prefixes = {
            "en": "[EN] ",
            "fr": "[FR] ",
            "de": "[DE] ",
            "es": "[ES] ",
            "pt": "[PT] ",
            "it": "[IT] ",
            "nl": "[NL] ",
            "da": "[DA] ",
            "fi": "[FI] ",
            "sv": "[SV] ",
        }
        prefix = prefixes.get(source_language, f"[{source_language.upper()}] ")

        # Simple "translation": add prefix and reverse text (fun!)
        if random.random() < 0.3:  # Sometimes do a "translation"
            translated = text[::-1]
        else:
            translated = text

        duration_ms = 10.0 * random.random()
        char_count = len(text)

        result = self._create_result(
            text=f"{prefix}{translated}" if source_language != target_language else text,
            source_language=source_language,
            target_language=target_language,
            duration_ms=duration_ms,
            char_count=char_count,
        )
        self._record_metrics(duration_ms, char_count, True)
        return result

    async def translate_many(
        self,
        texts: List[str],
        source_language: str,
        target_language: str = DEFAULT_LANGUAGE,
    ) -> List[TranslationResult]:
        """Mock batch translation."""
        self._batch_call_count += 1

        results = []
        for text in texts:
            result = await self.translate(text, source_language, target_language)
            results.append(result)

        return results

    async def _health_check_request(self) -> HealthCheckResult:
        """Health check for mock provider."""
        self._health_check_calls += 1
        return HealthCheckResult(
            healthy=not self._simulate_failure,
            provider=self._provider_type,
            message="Mock provider healthy",
            details={
                "call_count": self._call_count,
                "batch_call_count": self._batch_call_count,
                "health_check_count": self._health_check_calls,
            },
            checked_at=datetime.utcnow().isoformat(),
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get mock provider statistics."""
        return {
            "call_count": self._call_count,
            "batch_call_count": self._batch_call_count,
            "health_check_calls": self._health_check_calls,
            "failure_rate": self._failure_rate,
            "simulate_failure": self._simulate_failure,
        }


# ============================================================
# Provider Factory
# ============================================================

def create_translation_provider(
    config: TranslationConfig,
) -> TranslationProvider:
    """
    Factory function to create a translation provider.
    
    Args:
        config: Translation configuration
        
    Returns:
        TranslationProvider: The configured provider
        
    Raises:
        TranslationProviderError: If the provider type is unsupported
    """
    provider_type = config.provider

    if provider_type == TranslationProviderType.GOOGLE:
        return GoogleTranslateProvider(config)
    elif provider_type == TranslationProviderType.DEEPL:
        return DeepLProvider(config)
    elif provider_type == TranslationProviderType.MOCK:
        return MockTranslationProvider(config)
    elif provider_type == TranslationProviderType.AZURE:
        raise TranslationProviderError(
            "Azure Translator provider not yet implemented. "
            "Use GOOGLE (development) or DEEPL (production) instead.",
            provider=provider_type,
        )
    else:
        raise TranslationProviderError(
            f"Unsupported translation provider: {provider_type}",
            provider=provider_type,
        )


# ============================================================
# Export
# ============================================================

__all__ = [
    "RetryPolicy",
    "CircuitBreaker",
    "BaseTranslationProvider",
    "GoogleTranslateProvider",
    "DeepLProvider",
    "MockTranslationProvider",
    "create_translation_provider",
]