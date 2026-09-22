from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

import app.services.translation.service as translation_service_module
from app.services.translation.interface import (
    HealthCheckResult,
    TranslationConfig,
    TranslationError,
    TranslationProviderError,
    TranslationProviderType,
    TranslationRateLimitError,
    TranslationResult,
)
from app.services.translation.service import (
    CacheStatistics,
    MetricsSnapshot,
    TranslationCache,
    TranslationService,
)


def test_cache_statistics_rates():
    stats = CacheStatistics(
        size=5,
        max_size=10,
        hits=3,
        misses=1,
    )

    assert stats.hit_rate == 75.0
    assert stats.used_percent == 50.0


def test_cache_statistics_zero_denominators():
    stats = CacheStatistics()

    assert stats.hit_rate == 0.0
    assert stats.used_percent == 0.0


def test_metrics_snapshot_rates_and_dict():
    snapshot = MetricsSnapshot(
        total_requests=4,
        successful_requests=3,
        failed_requests=1,
        total_duration_ms=200.0,
        total_characters=100,
        provider="google",
    )

    assert snapshot.success_rate == 75.0
    assert snapshot.avg_duration_ms == 50.0

    data = snapshot.to_dict()

    assert data["total_requests"] == 4
    assert data["successful_requests"] == 3
    assert data["failed_requests"] == 1
    assert data["success_rate"] == 75.0
    assert data["avg_duration_ms"] == 50.0
    assert data["total_duration_ms"] == 200.0
    assert data["total_characters"] == 100
    assert data["provider"] == "google"


def test_translation_provider_error_preserves_metadata():
    error = TranslationProviderError(
        "Translation failed",
        provider=TranslationProviderType.GOOGLE,
        status_code=500,
        retry_after=10,
    )

    assert str(error) == "Translation failed"
    assert error.provider is TranslationProviderType.GOOGLE
    assert error.status_code == 500
    assert error.retry_after == 10


def test_translation_rate_limit_error_preserves_metadata():
    error = TranslationRateLimitError(
        "Rate limit exceeded",
        provider=TranslationProviderType.GOOGLE,
        retry_after=30,
        limit=100,
    )

    assert str(error) == "Rate limit exceeded"
    assert error.provider is TranslationProviderType.GOOGLE
    assert error.retry_after == 30
    assert error.limit == 100


def test_metrics_snapshot_zero_requests():
    snapshot = MetricsSnapshot()

    assert snapshot.success_rate == 0.0
    assert snapshot.avg_duration_ms == 0.0


@pytest.mark.asyncio
async def test_cache_miss_then_hit():
    cache = TranslationCache(max_size=10)

    result = TranslationResult(
        text="Bonjour",
        source_language="en",
        target_language="fr",
        success=True,
    )

    assert await cache.get("Hello", "en", "fr") is None

    await cache.set("Hello", "en", "fr", result)

    cached = await cache.get("Hello", "en", "fr")

    assert cached is result

    stats = await cache.get_stats()
    assert stats.size == 1
    assert stats.hits == 1
    assert stats.misses == 1


@pytest.mark.asyncio
async def test_cache_clear_resets_entries_and_statistics():
    cache = TranslationCache()

    result = TranslationResult(
        text="Bonjour",
        source_language="en",
        target_language="fr",
        success=True,
    )

    await cache.set("Hello", "en", "fr", result)
    await cache.get("Hello", "en", "fr")

    await cache.clear()

    stats = await cache.get_stats()

    assert stats.size == 0
    assert stats.hits == 0
    assert stats.misses == 0
    assert await cache.get("Hello", "en", "fr") is None


@pytest.mark.asyncio
async def test_cache_evicts_oldest_entry():
    cache = TranslationCache(max_size=2)

    result1 = TranslationResult(
        text="One",
        source_language="en",
        target_language="fr",
        success=True,
    )
    result2 = TranslationResult(
        text="Two",
        source_language="en",
        target_language="fr",
        success=True,
    )
    result3 = TranslationResult(
        text="Three",
        source_language="en",
        target_language="fr",
        success=True,
    )

    await cache.set("1", "en", "fr", result1)
    await cache.set("2", "en", "fr", result2)
    await cache.set("3", "en", "fr", result3)

    assert await cache.get("1", "en", "fr") is None
    assert await cache.get("2", "en", "fr") is result2
    assert await cache.get("3", "en", "fr") is result3


@pytest.mark.asyncio
async def test_cache_lru_moves_accessed_entry_to_end():
    cache = TranslationCache(max_size=2)

    result1 = TranslationResult(
        text="One",
        source_language="en",
        target_language="fr",
        success=True,
    )
    result2 = TranslationResult(
        text="Two",
        source_language="en",
        target_language="fr",
        success=True,
    )
    result3 = TranslationResult(
        text="Three",
        source_language="en",
        target_language="fr",
        success=True,
    )

    await cache.set("1", "en", "fr", result1)
    await cache.set("2", "en", "fr", result2)

    await cache.get("1", "en", "fr")
    await cache.set("3", "en", "fr", result3)

    assert await cache.get("1", "en", "fr") is result1
    assert await cache.get("2", "en", "fr") is None


@pytest.mark.asyncio
async def test_cache_expired_entry_is_miss():
    cache = TranslationCache(max_size=10, ttl_seconds=10)

    result = TranslationResult(
        text="Bonjour",
        source_language="en",
        target_language="fr",
        success=True,
    )

    await cache.set("Hello", "en", "fr", result)

    with patch("app.services.translation.service.datetime") as mock_datetime:
        mock_datetime.now.return_value.timestamp.return_value = datetime.now(UTC).timestamp() + 20

        assert await cache.get("Hello", "en", "fr") is None


@pytest.fixture
def provider():
    provider = Mock()
    provider.provider_type = TranslationProviderType.GOOGLE
    provider.translate = AsyncMock()
    provider.translate_many = AsyncMock()
    provider.health_check = AsyncMock()
    provider.close = AsyncMock()
    return provider


@pytest.fixture
def service(provider):
    return TranslationService(provider=provider)


def make_result(text="Bonjour", success=True, error=None):
    return TranslationResult(
        text=text,
        source_language="en",
        target_language="fr",
        success=success,
        error=error,
    )


@pytest.mark.asyncio
async def test_translate_rejects_closed_service(provider):
    service = TranslationService(provider=provider)
    service._closed = True

    with pytest.raises(TranslationError, match="Translation service is closed"):
        await service.translate("Hello", "en", "fr")


@pytest.mark.asyncio
async def test_translate_empty_text_returns_success_without_provider(provider):
    service = TranslationService(provider=provider)

    result = await service.translate("   ", "en", "fr")

    assert result.success is True
    assert result.text == "   "
    provider.translate.assert_not_awaited()


@pytest.mark.asyncio
async def test_translate_provider_success_records_metrics(provider):
    provider.translate.return_value = make_result()

    service = TranslationService(provider=provider)

    result = await service.translate("Hello", "en", "fr")

    assert result.success is True
    provider.translate.assert_awaited_once_with(
        text="Hello",
        source_language="en",
        target_language="fr",
    )

    metrics = await service.get_metrics()
    assert metrics.total_requests == 1
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 0
    assert metrics.total_characters == 5


@pytest.mark.asyncio
async def test_translate_provider_failure_returns_fallback_result(provider):
    error = RuntimeError("provider failed")
    provider.translate.side_effect = error

    service = TranslationService(provider=provider)

    result = await service.translate("Hello", "en", "fr")

    assert result.success is False
    assert result.text == "Hello"
    assert result.source_language == "en"
    assert result.target_language == "fr"
    assert result.error is error

    metrics = await service.get_metrics()
    assert metrics.total_requests == 1
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 1
    assert metrics.total_characters == 5


@pytest.mark.asyncio
async def test_translate_cache_hit_skips_provider(provider):
    cache = TranslationCache()

    cached_result = make_result(text="Bonjour")
    await cache.set("Hello", "en", "fr", cached_result)

    service = TranslationService(
        provider=provider,
        cache=cache,
    )

    result = await service.translate("Hello", "en", "fr")

    assert result is cached_result
    provider.translate.assert_not_awaited()


def test_translation_config_rejects_non_positive_timeout():
    with pytest.raises(ValueError, match="timeout must be greater than 0"):
        TranslationConfig(timeout=0)


def test_translation_config_rejects_negative_retry_count():
    with pytest.raises(ValueError, match="retry_count must be non-negative"):
        TranslationConfig(retry_count=-1)


def test_translation_config_rejects_non_positive_retry_delay():
    with pytest.raises(ValueError, match="retry_delay must be greater than 0"):
        TranslationConfig(retry_delay=0)


def test_translation_config_rejects_backoff_factor_below_one():
    with pytest.raises(ValueError, match="retry_backoff_factor must be >= 1.0"):
        TranslationConfig(retry_backoff_factor=0.5)


def test_translation_config_rejects_invalid_retry_jitter():
    with pytest.raises(ValueError, match="retry_jitter must be between 0 and 1.0"):
        TranslationConfig(retry_jitter=1.1)


def test_translation_config_rejects_non_positive_batch_size():
    with pytest.raises(ValueError, match="batch_max_size must be greater than 0"):
        TranslationConfig(batch_max_size=0)


@pytest.mark.asyncio
async def test_translate_caches_provider_result(provider):
    cache = TranslationCache()

    provider.translate.return_value = make_result(text="Bonjour")

    service = TranslationService(
        provider=provider,
        cache=cache,
    )

    result = await service.translate("Hello", "en", "fr")

    assert result.text == "Bonjour"

    cached = await cache.get("Hello", "en", "fr")

    assert cached is result
    provider.translate.assert_awaited_once_with(
        text="Hello",
        source_language="en",
        target_language="fr",
    )


@pytest.mark.asyncio
async def test_translate_many_rejects_closed_service(provider):
    service = TranslationService(provider=provider)
    service._closed = True

    with pytest.raises(TranslationError, match="Translation service is closed"):
        await service.translate_many(["Hello"], "en", "fr")


@pytest.mark.asyncio
async def test_translate_many_empty_list_returns_empty(provider):
    service = TranslationService(provider=provider)

    result = await service.translate_many([], "en", "fr")

    assert result == []
    provider.translate_many.assert_not_awaited()


@pytest.mark.asyncio
async def test_translate_many_handles_empty_items(provider):
    provider.translate_many.return_value = [
        make_result(text="Bonjour"),
    ]

    service = TranslationService(provider=provider)

    results = await service.translate_many(
        ["", "Hello", "   "],
        "en",
        "fr",
    )

    assert len(results) == 3
    assert results[0].text == ""
    assert results[0].success is True
    assert results[1].text == "Bonjour"
    assert results[2].text == "   "

    provider.translate_many.assert_awaited_once_with(
        texts=["Hello"],
        source_language="en",
        target_language="fr",
    )


@pytest.mark.asyncio
async def test_translate_many_provider_success(provider):
    provider.translate_many.return_value = [
        make_result(text="Bonjour"),
        make_result(text="Au revoir"),
    ]

    service = TranslationService(provider=provider)

    results = await service.translate_many(
        ["Hello", "Goodbye"],
        "en",
        "fr",
    )

    assert [result.text for result in results] == [
        "Bonjour",
        "Au revoir",
    ]

    provider.translate_many.assert_awaited_once_with(
        texts=["Hello", "Goodbye"],
        source_language="en",
        target_language="fr",
    )

    metrics = await service.get_metrics()
    assert metrics.total_requests == 1
    assert metrics.successful_requests == 1
    assert metrics.total_characters == len("Hello") + len("Goodbye")


@pytest.mark.asyncio
async def test_translate_many_uses_cached_results(provider):
    cache = TranslationCache()

    cached = make_result(text="Bonjour")
    await cache.set("Hello", "en", "fr", cached)

    provider.translate_many.return_value = [
        make_result(text="Au revoir"),
    ]

    service = TranslationService(
        provider=provider,
        cache=cache,
    )

    results = await service.translate_many(
        ["Hello", "Goodbye"],
        "en",
        "fr",
    )

    assert results[0] is cached
    assert results[1].text == "Au revoir"

    provider.translate_many.assert_awaited_once_with(
        texts=["Goodbye"],
        source_language="en",
        target_language="fr",
    )


@pytest.mark.asyncio
async def test_translate_many_provider_failure_returns_fallbacks(provider):
    error = RuntimeError("batch failed")
    provider.translate_many.side_effect = error

    service = TranslationService(provider=provider)

    results = await service.translate_many(
        ["Hello", "Goodbye"],
        "en",
        "fr",
    )

    assert len(results) == 2
    assert all(result.success is False for result in results)
    assert [result.text for result in results] == ["Hello", "Goodbye"]
    assert all(result.error is error for result in results)

    metrics = await service.get_metrics()
    assert metrics.failed_requests == 1


@pytest.mark.asyncio
async def test_health_check_when_service_closed(provider):
    service = TranslationService(provider=provider)
    service._closed = True

    result = await service.health_check()

    assert result.healthy is False
    assert result.provider == TranslationProviderType.GOOGLE
    assert result.message == "Translation service is closed"


@pytest.mark.asyncio
async def test_health_check_success_includes_service_metrics(provider):
    provider.health_check.return_value = HealthCheckResult(
        healthy=True,
        provider=TranslationProviderType.GOOGLE,
        latency_ms=12.5,
        message="OK",
        details={"backend": "available"},
    )

    service = TranslationService(provider=provider)

    result = await service.health_check()

    assert result.healthy is True
    assert result.latency_ms == 12.5
    assert result.message == "OK"
    assert result.details is not None
    assert result.details["backend"] == "available"
    assert "service_metrics" in result.details
    provider.health_check.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_check_provider_failure(provider):
    provider.health_check.side_effect = RuntimeError("health unavailable")

    service = TranslationService(provider=provider)

    result = await service.health_check()

    assert result.healthy is False
    assert result.provider == TranslationProviderType.GOOGLE
    assert result.message == "Health check failed: health unavailable"


@pytest.mark.asyncio
async def test_get_cache_stats_without_cache(provider):
    service = TranslationService(provider=provider)

    stats = await service.get_cache_stats()

    assert stats.size == 0
    assert stats.max_size == 0


@pytest.mark.asyncio
async def test_get_cache_stats_with_cache(provider):
    cache = TranslationCache(max_size=25, ttl_seconds=60)
    service = TranslationService(provider=provider, cache=cache)

    stats = await service.get_cache_stats()

    assert stats.size == 0
    assert stats.max_size == 25
    assert stats.ttl_seconds == 60


@pytest.mark.asyncio
async def test_service_stats(provider):
    cache = TranslationCache(max_size=10)
    service = TranslationService(provider=provider, cache=cache)

    stats = await service.get_service_stats()

    assert stats.provider == "google"
    assert stats.closed is False
    assert stats.uptime_seconds >= 0
    assert stats.cache.max_size == 10
    assert stats.metrics.total_requests == 0


@pytest.mark.asyncio
async def test_close_closes_provider_and_cache(provider):
    cache = TranslationCache()

    result = make_result()
    await cache.set("Hello", "en", "fr", result)

    service = TranslationService(
        provider=provider,
        cache=cache,
    )

    await service.close()

    assert service._closed is True
    provider.close.assert_awaited_once()

    stats = await cache.get_stats()
    assert stats.size == 0


@pytest.mark.asyncio
async def test_close_is_idempotent_for_provider(provider):
    service = TranslationService(provider=provider)

    await service.close()
    await service.close()

    provider.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_cache(provider):
    cache = TranslationCache()

    await cache.set("Hello", "en", "fr", make_result())

    service = TranslationService(
        provider=provider,
        cache=cache,
    )

    await service.clear_cache()

    stats = await cache.get_stats()
    assert stats.size == 0


def test_create_default_with_explicit_config_and_cache(provider):
    config = TranslationConfig(
        provider=TranslationProviderType.GOOGLE,
    )

    with patch(
        "app.services.translation.service.create_translation_provider",
        return_value=provider,
    ) as create_provider:
        service = TranslationService.create_default(
            config=config,
            enable_cache=True,
            cache_max_size=25,
            cache_ttl=60,
        )

    create_provider.assert_called_once_with(config)
    assert service._provider is provider
    assert service._cache is not None


def test_create_default_without_cache(provider):
    config = TranslationConfig(
        provider=TranslationProviderType.GOOGLE,
    )

    with patch(
        "app.services.translation.service.create_translation_provider",
        return_value=provider,
    ):
        service = TranslationService.create_default(
            config=config,
            enable_cache=False,
        )

    assert service._provider is provider
    assert service._cache is None


def test_create_default_loads_config_from_settings(provider):
    config = TranslationConfig(
        provider=TranslationProviderType.GOOGLE,
    )

    with (
        patch.object(
            TranslationService,
            "_load_config_from_settings",
            return_value=config,
        ) as load_config,
        patch(
            "app.services.translation.service.create_translation_provider",
            return_value=provider,
        ),
    ):
        service = TranslationService.create_default()

    load_config.assert_called_once()
    assert service._provider is provider


def test_load_config_from_settings_uses_settings():
    settings = Mock()
    settings.translation_provider = "deepl"
    settings.translation_timeout = 30
    settings.translation_retry_count = 5
    settings.translation_retry_delay = 2.0
    settings.translation_retry_backoff = 3.0
    settings.deepl_api_key = "deepl-key"
    settings.azure_translator_key = "azure-key"
    settings.azure_translator_endpoint = "https://azure.example"
    settings.azure_translator_region = "eastus"
    settings.google_cloud_project = "project"
    settings.google_application_credentials = "/credentials.json"

    with patch(
        "app.services.translation.service.settings",
        settings,
    ):
        config = TranslationService._load_config_from_settings()

    assert config.provider is TranslationProviderType.DEEPL
    assert config.timeout == 30
    assert config.retry_count == 5
    assert config.retry_delay == 2.0
    assert config.retry_backoff_factor == 3.0
    assert config.deepl_api_key == "deepl-key"
    assert config.azure_translator_key == "azure-key"
    assert config.azure_translator_endpoint == "https://azure.example"
    assert config.azure_translator_region == "eastus"
    assert config.google_cloud_project == "project"
    assert config.google_application_credentials == "/credentials.json"


def test_load_config_from_settings_invalid_provider_defaults_to_google():
    settings = SimpleNamespace(
        translation_provider="not-a-provider",
        translation_timeout=15,
        translation_retry_count=3,
        translation_retry_delay=1.0,
        translation_retry_backoff=2.0,
        deepl_api_key=None,
        azure_translator_key=None,
        azure_translator_endpoint=None,
        azure_translator_region=None,
        google_cloud_project=None,
        google_application_credentials=None,
    )

    with patch(
        "app.services.translation.service.settings",
        settings,
    ):
        config = TranslationService._load_config_from_settings()

    assert config.provider is TranslationProviderType.GOOGLE


@pytest.mark.asyncio
async def test_service_async_context_manager(provider):
    service = TranslationService(provider=provider)

    async with service as entered:
        assert entered is service
        assert service._closed is False

    provider.close.assert_awaited_once()
    assert service._closed is True


@pytest.mark.asyncio
async def test_get_translation_service_creates_singleton(provider):
    translation_service_module._service = None
    service = TranslationService(provider=provider)

    with patch.object(
        TranslationService,
        "create_default",
        return_value=service,
    ) as create_default:
        result = await translation_service_module.get_translation_service()

    assert result is service
    create_default.assert_called_once()

    translation_service_module._service = None


@pytest.mark.asyncio
async def test_get_translation_service_reuses_singleton(provider):
    existing = TranslationService(provider=provider)
    translation_service_module._service = existing

    with patch.object(
        TranslationService,
        "create_default",
    ) as create_default:
        result = await translation_service_module.get_translation_service()

    assert result is existing
    create_default.assert_not_called()

    translation_service_module._service = None


@pytest.mark.asyncio
async def test_translate_text_delegates_to_service():
    service = Mock()
    service.translate = AsyncMock(return_value=make_result(text="Bonjour"))

    with patch(
        "app.services.translation.service.get_translation_service",
        new=AsyncMock(return_value=service),
    ):
        result = await translation_service_module.translate_text(
            "Hello",
            "en",
            "fr",
        )

    assert result.text == "Bonjour"
    service.translate.assert_awaited_once_with(
        "Hello",
        "en",
        "fr",
    )


@pytest.mark.asyncio
async def test_translate_texts_delegates_to_service():
    service = Mock()
    service.translate_many = AsyncMock(
        return_value=[
            make_result(text="Bonjour"),
            make_result(text="Au revoir"),
        ]
    )

    with patch(
        "app.services.translation.service.get_translation_service",
        new=AsyncMock(return_value=service),
    ):
        results = await translation_service_module.translate_texts(
            ["Hello", "Goodbye"],
            "en",
            "fr",
        )

    assert [result.text for result in results] == [
        "Bonjour",
        "Au revoir",
    ]
    service.translate_many.assert_awaited_once_with(
        ["Hello", "Goodbye"],
        "en",
        "fr",
    )
