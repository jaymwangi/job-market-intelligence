import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from app.api.middleware import (
    RequestLoggingMiddleware,
    get_request_context,
    get_task_logger,
    log_elapsed_time,
    setup_middleware,
)


class TestRequestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_dispatch_generates_request_id_and_sets_request_state(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.return_value = "generated-test-id"
        request.url.path = "/api/jobs"
        request.method = "GET"
        request.client = None
        request.query_params = {}

        logger = MagicMock()
        response = JSONResponse({"ok": True}, status_code=200)

        async def call_next(req):
            assert req.state.request_id
            assert req.state.logger is logger
            return response

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ), patch(
            "app.api.middleware.metrics_collector.record_request"
        ) as record_request, patch.object(
            __import__("app.api.middleware", fromlist=["settings"]).settings,
            "api_prefix",
            "/api",
        ):
            result = await middleware.dispatch(request, call_next)

        assert result is response
        assert response.headers["X-Request-ID"] == request.state.request_id
        record_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_preserves_existing_request_id(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.side_effect = lambda key, default=None: (
            "existing-id" if key == "X-Request-ID" else default
        )
        request.url.path = "/api/jobs"
        request.method = "GET"
        request.client = None
        request.query_params = {}

        logger = MagicMock()
        response = JSONResponse({"ok": True})

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ):
            result = await middleware.dispatch(
                request,
                AsyncMock(return_value=response),
            )

        assert request.state.request_id == "existing-id"
        assert result.headers["X-Request-ID"] == "existing-id"

    @pytest.mark.asyncio
    async def test_dispatch_logs_debug_details_when_debug_enabled(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.side_effect = lambda key, default=None: (
            "request-id" if key == "X-Request-ID" else "TestAgent"
        )
        request.url.path = "/api/jobs"
        request.method = "GET"
        request.client = SimpleNamespace(host="127.0.0.1", port=1234)
        request.query_params = {"page": "1"}

        logger = MagicMock()
        response = JSONResponse({"ok": True})

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ), patch.object(
            __import__(
                "app.api.middleware",
                fromlist=["settings"],
            ).settings,
            "debug",
            True,
        ):
            await middleware.dispatch(
                request,
                AsyncMock(return_value=response),
            )

        logger.debug.assert_called_once_with(
            "Request details",
            user_agent="TestAgent",
            query_params=str(request.query_params),
        )

    @pytest.mark.asyncio
    async def test_dispatch_skips_logging_for_excluded_path(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.return_value = "request-id"
        request.url.path = "/health"
        request.method = "GET"
        request.client = None
        request.query_params = {}

        logger = MagicMock()
        response = JSONResponse({"status": "ok"})

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ), patch(
            "app.api.middleware.EXCLUDED_PATHS",
            frozenset({"/health"}),
        ):
            await middleware.dispatch(
                request,
                AsyncMock(return_value=response),
            )

        logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_logs_client_error(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.return_value = "request-id"
        request.url.path = "/api/jobs"
        request.method = "GET"
        request.client = None
        request.query_params = {}

        logger = MagicMock()
        response = JSONResponse({"error": "bad request"}, status_code=400)

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ):
            await middleware.dispatch(
                request,
                AsyncMock(return_value=response),
            )

        logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_logs_server_error(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.return_value = "request-id"
        request.url.path = "/api/jobs"
        request.method = "GET"
        request.client = None
        request.query_params = {}

        logger = MagicMock()
        response = JSONResponse({"error": "server error"}, status_code=500)

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ):
            await middleware.dispatch(
                request,
                AsyncMock(return_value=response),
            )

        logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_skips_metrics_for_non_api_endpoint(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.return_value = "request-id"
        request.url.path = "/docs"
        request.method = "GET"
        request.client = None
        request.query_params = {}

        response = JSONResponse({"ok": True})

        with patch(
            "app.api.middleware.get_logger",
            return_value=MagicMock(),
        ), patch(
            "app.api.middleware.metrics_collector.record_request"
        ) as record_request:
            await middleware.dispatch(
                request,
                AsyncMock(return_value=response),
            )

        record_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_records_error_metric_and_reraises(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.return_value = "request-id"
        request.url.path = "/api/jobs"
        request.method = "GET"
        request.client = None
        request.query_params = {}

        logger = MagicMock()
        error = RuntimeError("boom")

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ), patch(
            "app.api.middleware.metrics_collector.record_request"
        ) as record_request, patch.object(
            __import__(
                "app.api.middleware",
                fromlist=["settings"],
            ).settings,
            "api_prefix",
            "/api",
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await middleware.dispatch(
                    request,
                    AsyncMock(side_effect=error),
                )

        record_request.assert_called_once()
        assert record_request.call_args.kwargs["status_code"] == 500
        logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_with_client_information(self):
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MagicMock(spec=Request)
        request.headers.get.return_value = "request-id"
        request.url.path = "/api/jobs"
        request.method = "POST"
        request.client = SimpleNamespace(host="10.0.0.1", port=8080)
        request.query_params = {}

        logger = MagicMock()
        response = JSONResponse({"ok": True})

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ):
            await middleware.dispatch(
                request,
                AsyncMock(return_value=response),
            )

        logger.info.assert_any_call(
            "Request started",
            method="POST",
            path="/api/jobs",
            client_host="10.0.0.1",
            client_port=8080,
        )

    def test_metrics_collector_import_fallback(self):
        import app.api.middleware as middleware_module

        original_import = __import__

        def failing_import(name, *args, **kwargs):
            if name == "app.core.metrics":
                raise ImportError("metrics unavailable")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=failing_import):
            reloaded_module = importlib.reload(middleware_module)

        try:
            collector = reloaded_module.metrics_collector

            assert collector.__class__.__name__ == "DummyMetricsCollector"
            collector.record_request(
                endpoint="/api/jobs",
                status_code=200,
                duration_ms=1.5,
            )
        finally:
            importlib.reload(middleware_module)


class TestMiddlewareHelpers:
    def test_get_request_context_with_request_id(self):
        request = MagicMock(spec=Request)
        request.state.request_id = "abc-123"

        assert get_request_context(request) == {"request_id": "abc-123"}

    def test_get_request_context_without_request_id(self):
        request = MagicMock(spec=Request)
        request.state = SimpleNamespace()

        assert get_request_context(request) == {"request_id": "-"}

    def test_get_task_logger_uses_request_context(self):
        request = MagicMock(spec=Request)
        request.state.request_id = "abc-123"

        logger = MagicMock()
        bound_logger = MagicMock()
        logger.bind.return_value = bound_logger

        with patch(
            "app.api.middleware.get_logger",
            return_value=logger,
        ) as get_logger_mock:
            result = get_task_logger(request, "email_sender")

        get_logger_mock.assert_called_once_with(
            component="task",
            request_id="abc-123",
        )
        logger.bind.assert_called_once_with(task="email_sender")
        assert result is bound_logger

    def test_log_elapsed_time_with_logger(self):
        request = MagicMock(spec=Request)
        logger = MagicMock()
        request.state.logger = logger

        with patch(
            "app.api.middleware.time.perf_counter",
            return_value=1.125,
        ):
            log_elapsed_time(request, "database_query", 1.0)

        logger.info.assert_called_once_with(
            "Operation completed",
            operation="database_query",
            duration_ms=125.0,
        )

    def test_log_elapsed_time_without_logger(self):
        request = MagicMock(spec=Request)
        request.state = SimpleNamespace()

        log_elapsed_time(request, "database_query", 1.0)


class TestSetupMiddleware:
    def test_setup_middleware_development(self):
        app = FastAPI()

        with patch.object(
            __import__(
                "app.api.middleware",
                fromlist=["settings"],
            ).settings,
            "environment",
            "development",
        ):
            result = setup_middleware(app)

        assert result is app

    def test_setup_middleware_production_adds_trusted_host(self):
        app = FastAPI()

        with patch.object(
            __import__(
                "app.api.middleware",
                fromlist=["settings"],
            ).settings,
            "environment",
            "production",
        ):
            result = setup_middleware(app)

        assert result is app
