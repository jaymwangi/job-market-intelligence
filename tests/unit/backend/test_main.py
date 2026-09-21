import pytest
from fastapi import FastAPI

from app import main


def test_validate_configuration_accepts_valid_settings(monkeypatch):
    monkeypatch.setattr(main.settings, "database_url", "postgresql://localhost/test")
    monkeypatch.setattr(main.settings, "api_prefix", "/api/v1")
    monkeypatch.setattr(main.settings, "environment", "development")
    monkeypatch.setattr(main.settings, "db_pool_size", 5)
    monkeypatch.setattr(main.settings, "db_max_overflow", 10)
    monkeypatch.setattr(main.settings, "api_title", "Test API")
    monkeypatch.setattr(main.settings, "api_version", "1.0.0")
    monkeypatch.setattr(main.settings, "allowed_origins", ["http://localhost:3000"])

    main.validate_configuration()

def test_validate_configuration_rejects_missing_database_url(monkeypatch):
    monkeypatch.setattr(
        type(main.settings),
        "sqlalchemy_database_url",
        property(lambda self: ""),
    )

    with pytest.raises(ValueError, match="Database URL is not configured"):
        main.validate_configuration()

@pytest.mark.parametrize(
    ("attribute", "value", "message"),
    [
        ("api_prefix", "api/v1", "API prefix must start with '/'"),
        ("environment", "invalid", "Invalid environment"),
        ("db_pool_size", 0, "db_pool_size must be > 0"),
        ("db_max_overflow", -1, "db_max_overflow must be >= 0"),
        ("api_title", "", "api_title is not set"),
        ("api_version", "", "api_version is not set"),
    ],
)
def test_validate_configuration_rejects_invalid_settings(
    monkeypatch,
    attribute,
    value,
    message,
):
    monkeypatch.setattr(main.settings, attribute, value)

    with pytest.raises(ValueError, match=message):
        main.validate_configuration()


def test_validate_configuration_rejects_production_wildcard_origins(monkeypatch):
    monkeypatch.setattr(main.settings, "environment", "production")
    monkeypatch.setattr(main.settings, "allowed_origins", ["*"])

    with pytest.raises(ValueError, match="Wildcard origins not allowed in production"):
        main.validate_configuration()


def test_validate_configuration_rejects_production_validation_errors(monkeypatch):
    monkeypatch.setattr(main.settings, "environment", "production")
    monkeypatch.setattr(main.settings, "allowed_origins", ["https://example.com"])

    with pytest.raises(
        ValueError,
        match="DEBUG must be False in production",
    ):
        main.validate_configuration()


@pytest.mark.asyncio
async def test_lifespan_startup_and_shutdown(monkeypatch):
    monkeypatch.setattr(main, "validate_configuration", lambda: None)

    class FakeLogger:
        def bind(self, **kwargs):
            return self

        def info(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

    monkeypatch.setattr(main, "logger", FakeLogger())

    class FakeEngine:
        def __init__(self):
            self.disposed = False

        def dispose(self):
            self.disposed = True

    engine = FakeEngine()

    import sys
    import types

    fake_session = types.ModuleType("app.database.session")
    setattr(fake_session, "engine", engine)

    monkeypatch.setitem(sys.modules, "app.database.session", fake_session)

    async with main.lifespan(FastAPI()):
        pass

    assert engine.disposed is True


@pytest.mark.asyncio
async def test_lifespan_raises_when_configuration_is_invalid(monkeypatch):
    error = ValueError("invalid configuration")

    monkeypatch.setattr(
        main,
        "validate_configuration",
        lambda: (_ for _ in ()).throw(error),
    )

    class FakeLogger:
        def bind(self, **kwargs):
            return self

        def info(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

    monkeypatch.setattr(main, "logger", FakeLogger())

    with pytest.raises(ValueError, match="invalid configuration"):
        async with main.lifespan(FastAPI()):
            pass


@pytest.mark.asyncio
async def test_lifespan_handles_missing_database_engine(monkeypatch):
    monkeypatch.setattr(main, "validate_configuration", lambda: None)

    class FakeLogger:
        def bind(self, **kwargs):
            return self

        def info(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

    monkeypatch.setattr(main, "logger", FakeLogger())

    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "app.database.session":
            raise ImportError("database unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    async with main.lifespan(FastAPI()):
        pass


def test_root_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == main.settings.api_title
    assert data["version"] == main.settings.api_version
    assert data["environment"] == main.settings.environment
    assert data["status"] == "running"
    assert data["health"] == f"{main.settings.api_prefix}/health"
    assert data["api_prefix"] == main.settings.api_prefix

    assert data["docs"] == "/docs"
    assert data["redoc"] == "/redoc"
    assert data["openapi"] == "/openapi.json"


def test_debug_headers_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)

    response = client.get(
        "/debug/headers",
        headers={"X-Test-Header": "pytest"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["headers"]["x-test-header"] == "pytest"
    assert "request_id" in data


def test_debug_time_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)

    response = client.get("/debug/time")

    assert response.status_code == 200

    data = response.json()
    assert data["timezone"] == "UTC"
    assert "utc_time" in data
    assert data["utc_time"].endswith("+00:00")


def test_debug_ping_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)

    response = client.get("/debug/ping")

    assert response.status_code == 200

    data = response.json()
    assert data["pong"] is True
    assert "timestamp" in data
    assert data["timestamp"].endswith("+00:00")


def test_debug_routes_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)

    response = client.get("/debug/routes")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == len(data["routes"])
    assert data["count"] > 0

    paths = {
        route["path"]
        for route in data["routes"]
        if route["path"] is not None
    }

    assert "/" in paths
    assert "/debug/headers" in paths
    assert "/debug/time" in paths
    assert "/debug/ping" in paths
    assert "/debug/routes" in paths

def test_debug_routes_includes_websocket_route(monkeypatch):
    from fastapi.testclient import TestClient
    from starlette.routing import WebSocketRoute

    async def websocket_endpoint(websocket):
        await websocket.accept()
        await websocket.close()

    websocket_route = WebSocketRoute(
        "/test-websocket",
        endpoint=websocket_endpoint,
        name="test_websocket",
    )

    monkeypatch.setattr(
        main.app.router,
        "routes",
        [*main.app.router.routes, websocket_route],
    )

    client = TestClient(main.app)

    response = client.get("/debug/routes")

    assert response.status_code == 200

    data = response.json()

    websocket_routes = [
        route
        for route in data["routes"]
        if route["type"] == "WebSocketRoute"
    ]

    assert websocket_routes == [
        {
            "type": "WebSocketRoute",
            "path": "/test-websocket",
            "name": "test_websocket",
            "methods": ["WEBSOCKET"],
        }
    ]