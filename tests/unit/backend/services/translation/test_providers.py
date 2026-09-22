from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from app.services.translation.interface import (
    HealthCheckResult,
    TranslationConfig,
    TranslationProviderError,
    TranslationProviderType,
    TranslationRateLimitError,
    TranslationTimeoutError,
)
from app.services.translation.providers import (
    BaseTranslationProvider,
    CircuitBreaker,
    DeepLProvider,
    GoogleTranslateProvider,
    MockTranslationProvider,
    RetryPolicy,
    create_translation_provider,
)

# ============================================================
# RetryPolicy
# ============================================================


class TestRetryPolicy:
    def test_defaults_are_valid(self):
        policy = RetryPolicy()

        assert policy.attempts == 3
        assert policy.initial_delay == 1.0
        assert policy.backoff == 2.0
        assert policy.jitter == 0.1

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"attempts": -1}, "attempts must be non-negative"),
            ({"initial_delay": 0}, "initial_delay must be greater than 0"),
            ({"backoff": 0.5}, "backoff must be >= 1.0"),
            ({"jitter": -0.1}, "jitter must be between 0 and 1.0"),
            ({"jitter": 1.1}, "jitter must be between 0 and 1.0"),
        ],
    )
    def test_rejects_invalid_values(self, kwargs, message):
        with pytest.raises(ValueError, match=message):
            RetryPolicy(**kwargs)


# ============================================================
# CircuitBreaker
# ============================================================


class TestCircuitBreaker:
    def test_closed_breaker_allows_requests(self):
        breaker = CircuitBreaker()

        assert breaker.allow_request() is True
        assert breaker.is_open is False
        assert breaker.is_half_open is False

    def test_failure_threshold_opens_breaker(self):
        breaker = CircuitBreaker(failure_threshold=2)

        breaker.record_failure()
        assert breaker.is_open is False

        breaker.record_failure()

        assert breaker.is_open is True
        assert breaker.allow_request() is False

    def test_open_breaker_enters_half_open_after_recovery_timeout(self):
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=10,
        )

        breaker.record_failure()

        with patch(
            "app.services.translation.providers.time.time",
            return_value=breaker._last_failure_time + 11,
        ):
            assert breaker.allow_request() is True

        assert breaker.is_half_open is True

    def test_half_open_attempts_are_counted_by_successes(self):
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0,
            half_open_max_attempts=2,
        )

        breaker.record_failure()

        with patch(
            "app.services.translation.providers.time.time",
            return_value=breaker._last_failure_time + 1,
        ):
            assert breaker.allow_request() is True

        assert breaker.is_half_open is True

        breaker.record_success()
        assert breaker.is_half_open is True
        assert breaker.allow_request() is True

        breaker.record_success()

        assert breaker.is_half_open is False
        assert breaker.is_open is False
        assert breaker._failures == 0

    def test_reset_restores_closed_state(self):
        breaker = CircuitBreaker(failure_threshold=1)

        breaker.record_failure()
        assert breaker.is_open is True

        breaker.reset()

        assert breaker.is_open is False
        assert breaker.is_half_open is False
        assert breaker._failures == 0
        assert breaker._half_open_attempts == 0
        assert breaker._last_failure_time == 0.0


# ============================================================
# BaseTranslationProvider
# ============================================================


class ConcreteProvider(BaseTranslationProvider):
    def __init__(self, config):
        super().__init__(config)
        self._provider_type = TranslationProviderType.MOCK

    async def _health_check_request(self) -> HealthCheckResult:
        return HealthCheckResult(
            healthy=True,
            provider=self.provider_type,
            latency_ms=12.5,
            message="OK",
            details={"test": True},
        )


class TestBaseTranslationProvider:
    @pytest.fixture
    def provider(self):
        return ConcreteProvider(TranslationConfig())

    def test_initializes_provider_state(self, provider):
        assert provider.provider_type == TranslationProviderType.MOCK
        assert provider._session is None
        assert provider._closed is False

        metrics = provider.get_metrics()

        assert metrics["total_calls"] == 0
        assert metrics["successful_calls"] == 0
        assert metrics["failed_calls"] == 0
        assert metrics["avg_duration_ms"] == 0
        assert metrics["success_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_session_creates_and_reuses_session(self, provider):
        session1 = await provider._get_session()
        session2 = await provider._get_session()

        assert session1 is session2

        await provider.close()

    @pytest.mark.asyncio
    async def test_close_closes_session(self, provider):
        session = await provider._get_session()

        assert session.closed is False

        await provider.close()

        assert session.closed is True
        assert provider._closed is True

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_provider(self, provider):
        await provider._get_session()

        async with provider as entered:
            assert entered is provider

        assert provider._closed is True

    @pytest.mark.asyncio
    async def test_base_health_check_request_raises(self, provider):
        with pytest.raises(NotImplementedError):
            await BaseTranslationProvider._health_check_request(provider)

    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        result = await provider.health_check()

        assert result.healthy is True
        assert result.provider == TranslationProviderType.MOCK
        assert result.latency_ms == 12.5
        assert result.message == "OK"
        assert result.details == {"test": True}
        assert result.checked_at is not None

    @pytest.mark.asyncio
    async def test_health_check_when_closed(self, provider):
        provider._closed = True

        result = await provider.health_check()

        assert result.healthy is False
        assert result.provider == TranslationProviderType.MOCK
        assert result.message == "Provider is closed"

    @pytest.mark.asyncio
    async def test_health_check_handles_exception(self, provider):
        async def fail():
            raise RuntimeError("health failure")

        provider._health_check_request = fail

        result = await provider.health_check()

        assert result.healthy is False
        assert result.message == "health failure"

    def test_create_result_success(self, provider):
        result = provider._create_result(
            text="Bonjour",
            source_language="fr",
            target_language="en",
            detected_language="fr",
            duration_ms=10.5,
            char_count=7,
        )

        assert result.text == "Bonjour"
        assert result.source_language == "fr"
        assert result.target_language == "en"
        assert result.detected_language == "fr"
        assert result.duration_ms == 10.5
        assert result.character_count == 7
        assert result.provider == TranslationProviderType.MOCK
        assert result.success is True
        assert result.error is None

    def test_create_result_error(self, provider):
        error = RuntimeError("failed")

        result = provider._create_result(
            text="Hello",
            source_language="en",
            target_language="fr",
            error=error,
        )

        assert result.success is False
        assert result.error is error

    def test_record_metrics_success_and_failure(self, provider):
        provider._record_metrics(10.0, 5, True)
        provider._record_metrics(20.0, 10, False)

        metrics = provider.get_metrics()

        assert metrics["total_calls"] == 2
        assert metrics["successful_calls"] == 1
        assert metrics["failed_calls"] == 1
        assert metrics["total_duration_ms"] == 30.0
        assert metrics["total_characters"] == 15
        assert metrics["avg_duration_ms"] == 15.0
        assert metrics["success_rate"] == 50.0


# ============================================================
# GoogleTranslateProvider
# ============================================================


class TestGoogleTranslateProvider:
    @pytest.fixture
    def provider(self):
        return GoogleTranslateProvider(TranslationConfig())

    @pytest.mark.asyncio
    async def test_empty_translation_returns_original_text(self, provider):
        result = await provider.translate("", "en", "fr")

        assert result.text == ""
        assert result.success is True
        assert result.source_language == "en"
        assert result.target_language == "fr"

    @pytest.mark.asyncio
    async def test_translate_timeout_raises_translation_timeout_error(self, provider):
        translator = Mock()
        translator.translate = AsyncMock(side_effect=TimeoutError("timed out"))
        provider._translator = translator

        with pytest.raises(Exception, match="Google Translate timeout"):
            await provider.translate("Hello", "fr", "en")

        metrics = provider.get_metrics()
        assert metrics["failed_calls"] == 1

    @pytest.mark.asyncio
    async def test_translate_generic_exception_returns_original_text(self, provider):
        translator = Mock()
        translator.translate = AsyncMock(side_effect=RuntimeError("API failed"))
        provider._translator = translator

        result = await provider.translate("Hello", "fr", "en")

        assert result.success is False
        assert result.text == "Hello"
        assert isinstance(result.error, RuntimeError)
        assert str(result.error) == "API failed"

    @pytest.mark.asyncio
    async def test_health_check_reports_exception(self, provider):
        async def failing_translate(text, source_language, target_language):
            raise RuntimeError("health check failed")

        provider.translate = cast(Any, failing_translate)

        result = await provider._health_check_request()

        assert result.healthy is False
        assert result.message == "health check failed"
        assert result.provider == TranslationProviderType.GOOGLE

    @pytest.mark.asyncio
    async def test_translate_uses_translator(self, provider):
        translator = Mock()
        translator.translate = AsyncMock(
            return_value=SimpleNamespace(
                text="Bonjour",
                src="fr",
            )
        )

        provider._translator = translator

        result = await provider.translate("Hello", "fr", "en")

        assert result.success is True
        assert result.text == "Bonjour"
        assert result.detected_language == "fr"
        translator.translate.assert_called_once_with(
            "Hello",
            dest="en",
            src="fr",
        )

    @pytest.mark.asyncio
    async def test_translate_uses_default_source_behavior(self, provider):
        translator = Mock()
        translator.translate = AsyncMock(
            return_value=SimpleNamespace(
                text="Bonjour",
                src="fr",
            )
        )

        provider._translator = translator

        with patch(
            "app.services.translation.providers.HAS_GOOGLETRANS",
            True,
        ):
            await provider.translate("Hello", "en", "fr")

        translator.translate.assert_called_once_with(
            "Hello",
            dest="fr",
        )

    @pytest.mark.asyncio
    async def test_get_translator_raises_when_dependency_missing(self, provider):
        provider._translator = None

        with (
            patch(
                "app.services.translation.providers.HAS_GOOGLETRANS",
                False,
            ),
            patch(
                "builtins.__import__",
                side_effect=ImportError("googletrans missing"),
            ),
        ):
            with pytest.raises(
                TranslationProviderError,
                match="googletrans is not installed",
            ):
                provider._get_translator()

    @pytest.mark.asyncio
    async def test_translate_many_preserves_order(self, provider):
        async def fake_translate(text, source_language, target_language):
            return provider._create_result(
                text=f"translated-{text}",
                source_language=source_language,
                target_language=target_language,
            )

        provider.translate = fake_translate

        results = await provider.translate_many(
            ["One", "Two"],
            "en",
            "fr",
        )

        assert [result.text for result in results] == [
            "translated-One",
            "translated-Two",
        ]

    @pytest.mark.asyncio
    async def test_health_check_uses_translation(self, provider):
        async def fake_translate(text, source_language, target_language):
            return SimpleNamespace(
                success=True,
                duration_ms=7.5,
            )

        provider.translate = cast(Any, fake_translate)

        result = await provider._health_check_request()

        assert result.healthy is True
        assert result.latency_ms is not None
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_health_check_reports_failed_translation(self, provider):
        async def fake_translate(text, source_language, target_language):
            return SimpleNamespace(
                success=False,
                duration_ms=5.0,
            )

        provider.translate = cast(Any, fake_translate)

        result = await provider._health_check_request()

        assert result.healthy is False
        assert result.latency_ms is not None
        assert result.latency_ms >= 0

    def test_get_translator_lazy_import_succeeds_when_dependency_was_missing(self, provider):
        fake_translator = Mock()

        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "googletrans":
                return SimpleNamespace(Translator=lambda: fake_translator)
            return real_import(name, *args, **kwargs)

        with (
            patch(
                "app.services.translation.providers.HAS_GOOGLETRANS",
                False,
            ),
            patch("builtins.__import__", side_effect=fake_import),
        ):
            result = provider._get_translator()

        assert result is fake_translator
        assert provider._translator is fake_translator

    def test_get_translator_raises_when_translator_class_is_none(self, provider):
        provider._translator = None

        with (
            patch(
                "app.services.translation.providers.HAS_GOOGLETRANS",
                True,
            ),
            patch(
                "app.services.translation.providers.Translator",
                None,
            ),
        ):
            with pytest.raises(
                TranslationProviderError,
                match="googletrans is not installed",
            ):
                provider._get_translator()

    def test_get_translator_instantiates_available_translator_class(self, provider):
        fake_translator = Mock()
        fake_translator_class = Mock(return_value=fake_translator)

        provider._translator = None

        with (
            patch(
                "app.services.translation.providers.HAS_GOOGLETRANS",
                True,
            ),
            patch(
                "app.services.translation.providers.Translator",
                fake_translator_class,
            ),
        ):
            result = provider._get_translator()

        assert result is fake_translator
        assert provider._translator is fake_translator
        fake_translator_class.assert_called_once_with()

    def test_module_import_handles_missing_googletrans(self):
        import importlib.util
        from pathlib import Path

        import app.services.translation.providers as providers_module

        module_path = Path(providers_module.__file__)
        spec = importlib.util.spec_from_file_location(
            "test_providers_missing_googletrans",
            module_path,
        )
        assert spec is not None
        assert spec.loader is not None

        test_module = importlib.util.module_from_spec(spec)

        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "googletrans":
                raise ImportError("googletrans missing")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            spec.loader.exec_module(test_module)

        assert test_module.HAS_GOOGLETRANS is False
        assert test_module.Translator is None


# ============================================================
# DeepLProvider
# ============================================================


class FakeResponse:
    def __init__(
        self,
        status=200,
        json_data=None,
        text_data="",
        headers=None,
    ):
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._json_data

    async def text(self):
        return self._text_data


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []
        self.closed = False

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

    async def close(self):
        self.closed = True


class TestDeepLProvider:
    @staticmethod
    def set_fake_session(provider, session: Any) -> None:
        provider._session = cast(Any, session)

    def test_requires_api_key(self):
        with pytest.raises(
            TranslationProviderError,
            match="DeepL API key is required",
        ):
            DeepLProvider(TranslationConfig())

    def test_accepts_explicit_api_key(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        assert provider.provider_type == TranslationProviderType.DEEPL
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.deepl.com/v2"

    @pytest.mark.asyncio
    async def test_empty_translation_returns_original_text(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        result = await provider.translate("", "en", "fr")

        assert result.text == ""
        assert result.success is True

    @pytest.mark.asyncio
    async def test_translate_success(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
            base_url="https://example.test/v2/",
        )

        response = FakeResponse(
            status=200,
            json_data={
                "translations": [
                    {
                        "text": "Bonjour",
                        "detected_source_language": "FR",
                    }
                ]
            },
        )

        session = FakeSession(response)
        self.set_fake_session(provider, session)

        result = await provider.translate("Hello", "en", "fr")

        assert result.success is True
        assert result.text == "Bonjour"
        assert result.detected_language == "fr"
        assert result.provider == TranslationProviderType.DEEPL

        url, kwargs = session.calls[0]

        assert url == "https://example.test/v2/translate"
        assert kwargs["data"]["auth_key"] == "test-key"
        assert kwargs["data"]["text"] == "Hello"
        assert kwargs["data"]["target_lang"] == "FR"
        assert "source_lang" not in kwargs["data"]

    @pytest.mark.asyncio
    async def test_translate_rejects_when_circuit_breaker_is_open(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )
        provider._circuit_breaker.record_failure()
        provider._circuit_breaker.record_failure()
        provider._circuit_breaker.record_failure()
        provider._circuit_breaker.record_failure()
        provider._circuit_breaker.record_failure()

        with pytest.raises(
            TranslationProviderError,
            match="Circuit breaker is open",
        ):
            await provider.translate("Hello", "en", "fr")

    @pytest.mark.asyncio
    async def test_translate_sends_explicit_source_language(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )
        response = FakeResponse(
            status=200,
            json_data={
                "translations": [
                    {
                        "text": "Bonjour",
                        "detected_source_language": "EN",
                    }
                ]
            },
        )
        session = FakeSession(response)
        self.set_fake_session(provider, session)

        result = await provider.translate("Hello", "sw", "fr")

        assert result.success is True
        assert session.calls[0][1]["data"]["source_lang"] == "SW"

    @pytest.mark.asyncio
    async def test_translate_timeout_raises_translation_timeout_error(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        class TimeoutSession:
            closed = False

            def post(self, url, **kwargs):
                raise TimeoutError("timed out")

        self.set_fake_session(provider, TimeoutSession())

        with pytest.raises(TranslationTimeoutError, match="DeepL translation timeout"):
            await provider.translate("Hello", "en", "fr")

        assert provider.get_metrics()["failed_calls"] == 1

    @pytest.mark.asyncio
    async def test_translate_client_error_raises_provider_error(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        class ClientErrorSession:
            closed = False

            def post(self, url, **kwargs):
                raise aiohttp.ClientError("connection failed")

        self.set_fake_session(provider, ClientErrorSession())

        with pytest.raises(
            TranslationProviderError,
            match="DeepL client error: connection failed",
        ):
            await provider.translate("Hello", "en", "fr")

        assert provider.get_metrics()["failed_calls"] == 1

    @pytest.mark.asyncio
    async def test_translate_generic_exception_returns_original_text(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        class FailingSession:
            closed = False

            def post(self, url, **kwargs):
                raise RuntimeError("unexpected failure")

        self.set_fake_session(provider, FailingSession())

        result = await provider.translate("Hello", "en", "fr")

        assert result.success is False
        assert result.text == "Hello"
        assert isinstance(result.error, RuntimeError)
        assert str(result.error) == "unexpected failure"

    @pytest.mark.asyncio
    async def test_translate_batch_empty_returns_empty_list(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        results = await provider._translate_batch([], "en", "fr")

        assert results == []

    @pytest.mark.asyncio
    async def test_translate_batch_sends_explicit_source_language(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )
        response = FakeResponse(
            status=200,
            json_data={
                "translations": [
                    {"text": "Bonjour"},
                    {"text": "Au revoir"},
                ]
            },
        )
        session = FakeSession(response)
        self.set_fake_session(provider, session)

        results = await provider._translate_batch(
            ["Hello", "Goodbye"],
            "sw",
            "fr",
        )

        assert [result.text for result in results] == [
            "Bonjour",
            "Au revoir",
        ]
        assert session.calls[0][1]["data"]["source_lang"] == "SW"

    @pytest.mark.asyncio
    async def test_health_check_reports_exception(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        async def failing_translate(text, source_language, target_language):
            raise RuntimeError("health check failed")

        provider.translate = cast(Any, failing_translate)

        result = await provider._health_check_request()

        assert result.healthy is False
        assert result.message == "health check failed"
        assert result.provider == TranslationProviderType.DEEPL

    @pytest.mark.asyncio
    async def test_translate_many_preserves_empty_items(self):
        provider = DeepLProvider(
            TranslationConfig(batch_max_size=2),
            api_key="test-key",
        )

        fallback_results = [
            provider._create_result("Bonjour", "en", "fr"),
            provider._create_result("Au revoir", "en", "fr"),
        ]
        provider.translate = AsyncMock(side_effect=fallback_results)

        results = await provider.translate_many(
            ["Hello", "", "Goodbye"],
            "en",
            "fr",
        )

        assert len(results) == 3
        assert results[0].text == "Bonjour"
        assert results[1].text == ""
        assert results[2].text == "Au revoir"

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        async def fake_translate(text, source_language, target_language):
            return provider._create_result(
                text="Bonjour",
                source_language=source_language,
                target_language=target_language,
            )

        provider.translate = cast(Any, fake_translate)

        result = await provider._health_check_request()

        assert result.healthy is True
        assert result.provider == TranslationProviderType.DEEPL
        assert result.latency_ms is not None
        assert result.latency_ms >= 0
        assert result.message == "OK"
        assert result.checked_at is not None

    @pytest.mark.asyncio
    async def test_translate_rate_limit_raises(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        response = FakeResponse(
            status=429,
            text_data="rate limited",
            headers={"Retry-After": "10"},
        )

        self.set_fake_session(provider, FakeSession(response))

        with pytest.raises(TranslationRateLimitError) as exc_info:
            await provider.translate("Hello", "en", "fr")

        assert exc_info.value.retry_after == 10
        assert provider._circuit_breaker._failures >= 1

    @pytest.mark.asyncio
    async def test_translate_http_error_returns_failed_result(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        response = FakeResponse(
            status=500,
            text_data="server error",
        )

        self.set_fake_session(provider, FakeSession(response))

        result = await provider.translate("Hello", "en", "fr")

        assert result.success is False
        assert result.text == "Hello"
        assert isinstance(result.error, TranslationProviderError)
        assert "DeepL API error 500" in str(result.error)

    @pytest.mark.asyncio
    async def test_translate_many_empty_input(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        assert await provider.translate_many([], "en", "fr") == []

    @pytest.mark.asyncio
    async def test_translate_many_all_empty_values(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        results = await provider.translate_many(
            ["", "   ", ""],
            "en",
            "fr",
        )

        assert len(results) == 3
        assert all(result.success for result in results)

    @pytest.mark.asyncio
    async def test_translate_many_batch_success(self):
        provider = DeepLProvider(
            TranslationConfig(batch_max_size=2),
            api_key="test-key",
        )

        batches = [
            [
                provider._create_result("Un", "en", "fr"),
                provider._create_result("Deux", "en", "fr"),
            ],
            [
                provider._create_result("Trois", "en", "fr"),
            ],
        ]

        async def fake_batch(texts, source_language, target_language):
            return batches.pop(0)

        provider._translate_batch = cast(Any, fake_batch)

        results = await provider.translate_many(
            ["One", "Two", "Three"],
            "en",
            "fr",
        )

        assert [result.text for result in results] == [
            "Un",
            "Deux",
            "Trois",
        ]

    @pytest.mark.asyncio
    async def test_translate_batch_empty(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        assert await provider._translate_batch([], "en", "fr") == []

    @pytest.mark.asyncio
    async def test_translate_batch_success(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        response = FakeResponse(
            status=200,
            json_data={
                "translations": [
                    {"text": "Un"},
                    {"text": "Deux"},
                ]
            },
        )

        self.set_fake_session(provider, FakeSession(response))

        results = await provider._translate_batch(
            ["One", "Two"],
            "en",
            "fr",
        )

        assert [result.text for result in results] == ["Un", "Deux"]

    @pytest.mark.asyncio
    async def test_translate_batch_rate_limit(self):
        provider = DeepLProvider(
            TranslationConfig(),
            api_key="test-key",
        )

        self.set_fake_session(
            provider,
            FakeSession(
                FakeResponse(
                    status=429,
                    headers={"Retry-After": "10"},
                )
            ),
        )

        with pytest.raises(TranslationRateLimitError):
            await provider._translate_batch(["Hello"], "en", "fr")

    @pytest.mark.asyncio
    async def test_translate_batch_http_error_falls_back_to_individual(self):
        provider = DeepLProvider(
            TranslationConfig(batch_max_size=2),
            api_key="test-key",
        )

        self.set_fake_session(
            provider,
            FakeSession(
                FakeResponse(
                    status=400,
                    text_data="bad request",
                )
            ),
        )

        fallback_results = [
            provider._create_result("Bonjour", "en", "fr"),
            provider._create_result("Au revoir", "en", "fr"),
        ]

        provider.translate = AsyncMock(side_effect=fallback_results)

        results = await provider._translate_batch(
            ["Hello", "Goodbye"],
            "en",
            "fr",
        )

        assert [result.text for result in results] == [
            "Bonjour",
            "Au revoir",
        ]
        assert provider.translate.await_count == 2


# ============================================================
# MockTranslationProvider
# ============================================================


class TestMockTranslationProvider:
    @pytest.fixture
    def provider(self):
        return MockTranslationProvider(TranslationConfig())

    @pytest.mark.asyncio
    async def test_empty_translation_succeeds(self, provider):
        result = await provider.translate("", "en", "fr")

        assert result.success is True
        assert result.text == ""

    @pytest.mark.asyncio
    async def test_translation_returns_result(self, provider):
        result = await provider.translate("Hello", "en", "fr")

        assert result.success is True
        assert result.text
        assert result.source_language == "en"
        assert result.target_language == "fr"

    @pytest.mark.asyncio
    async def test_translation_can_reverse_text(self, provider):
        with patch(
            "app.services.translation.providers.random.random",
            return_value=0.1,
        ):
            result = await provider.translate("Hello", "en", "fr")

        assert result.success is True
        assert result.text == "[EN] olleH"

    @pytest.mark.asyncio
    async def test_same_source_and_target(self, provider):
        result = await provider.translate("Hello", "en", "en")

        assert result.success is True
        assert result.text

    def test_failure_rate_is_clamped(self, provider):
        provider.set_failure_rate(-1)
        assert provider._failure_rate == 0

        provider.set_failure_rate(2)
        assert provider._failure_rate == 1

        provider.set_failure_rate(0.25)
        assert provider._failure_rate == 0.25

    @pytest.mark.asyncio
    async def test_simulated_failure(self, provider):
        provider.set_simulate_failure(True)

        with pytest.raises(
            TranslationProviderError,
            match="Mock translation failure",
        ):
            await provider.translate("Hello", "en", "fr")

    @pytest.mark.asyncio
    async def test_failure_rate_can_trigger_failure(self, provider):
        provider.set_failure_rate(1.0)

        with pytest.raises(TranslationProviderError):
            await provider.translate("Hello", "en", "fr")

    @pytest.mark.asyncio
    async def test_translate_many(self, provider):
        results = await provider.translate_many(
            ["One", "Two"],
            "en",
            "fr",
        )

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_health_check(self, provider):
        result = await provider.health_check()

        assert result.healthy is True
        assert result.provider == TranslationProviderType.MOCK

    @pytest.mark.asyncio
    async def test_health_check_reports_failure_mode(self, provider):
        provider.set_simulate_failure(True)

        result = await provider.health_check()

        assert result.healthy is False

    def test_get_stats(self, provider):
        provider.set_failure_rate(0.5)
        provider.set_simulate_failure(True)

        stats = provider.get_stats()

        assert stats["failure_rate"] == 0.5
        assert stats["simulate_failure"] is True


# ============================================================
# Factory
# ============================================================


class TestCreateTranslationProvider:
    def test_creates_google_provider(self):
        provider = create_translation_provider(
            TranslationConfig(provider=TranslationProviderType.GOOGLE)
        )

        assert isinstance(provider, GoogleTranslateProvider)

    def test_creates_mock_provider(self):
        provider = create_translation_provider(
            TranslationConfig(provider=TranslationProviderType.MOCK)
        )

        assert isinstance(provider, MockTranslationProvider)

    def test_creates_deepl_provider(self):
        provider = create_translation_provider(
            TranslationConfig(
                provider=TranslationProviderType.DEEPL,
                deepl_api_key="test-key",
            )
        )

        assert isinstance(provider, DeepLProvider)

    def test_azure_provider_is_explicitly_not_implemented(self):
        with pytest.raises(
            TranslationProviderError,
            match="Azure Translator provider not yet implemented",
        ):
            create_translation_provider(
                TranslationConfig(
                    provider=TranslationProviderType.AZURE,
                )
            )

    def test_unsupported_provider_raises(self):
        config = Mock()
        config.provider = "unsupported"

        with pytest.raises(
            TranslationProviderError,
            match="Unsupported translation provider",
        ):
            create_translation_provider(config)
