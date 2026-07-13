"""
Unit tests for API exception handlers.
"""

from datetime import datetime
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request

from app.api.exception_handlers import (
    database_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)


class TestExceptionHandlers:
    """Test suite for exception handlers."""

    @pytest.fixture
    def app(self):
        """Create a FastAPI app with exception handlers registered."""
        app = FastAPI()

        # Register handlers using the exception_handler decorator
        @app.exception_handler(RequestValidationError)
        async def handle_validation(request: Request, exc: RequestValidationError):
            return await validation_exception_handler(request, exc)

        @app.exception_handler(SQLAlchemyError)
        async def handle_database(request: Request, exc: SQLAlchemyError):
            return await database_exception_handler(request, exc)

        @app.exception_handler(Exception)
        async def handle_general(request: Request, exc: Exception):
            return await general_exception_handler(request, exc)

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client that doesn't re-raise exceptions."""
        return TestClient(app, raise_server_exceptions=False)

    def test_validation_exception_handler(self, app, client):
        """Test validation exception handler."""

        class TestModel(BaseModel):
            name: str
            age: int

        @app.post("/test-validation")
        def test_endpoint(data: TestModel):
            return {"status": "ok"}

        response = client.post("/test-validation", json={"name": "Test"})
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Validation error"
        assert "errors" in data
        assert "status_code" in data
        assert data["status_code"] == 422
        assert "path" in data
        assert "timestamp" in data

    def test_database_exception_handler(self, app, client):
        """Test database exception handler."""

        @app.get("/test-db-error")
        def test_endpoint():
            raise SQLAlchemyError("Connection failed")

        response = client.get("/test-db-error")
        assert response.status_code == 500

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "A database error occurred. Please try again later."
        assert "status_code" in data
        assert data["status_code"] == 500
        assert "path" in data
        assert "timestamp" in data

    def test_general_exception_handler(self, app, client):
        """Test general exception handler."""

        @app.get("/test-general-error")
        def test_endpoint():
            raise ValueError("Something went wrong")

        response = client.get("/test-general-error")
        assert response.status_code == 500

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "An unexpected error occurred. Please try again later."
        assert "status_code" in data
        assert data["status_code"] == 500
        assert "path" in data
        assert "timestamp" in data

    def test_validation_exception_with_multiple_errors(self, app, client):
        """Test validation exception with multiple errors."""

        class TestModel(BaseModel):
            name: str
            age: int
            email: str

        @app.post("/test-validation-multiple")
        def test_endpoint(data: TestModel):
            return {"status": "ok"}

        response = client.post("/test-validation-multiple", json={})
        assert response.status_code == 422

        data = response.json()
        assert len(data["errors"]) >= 3

    def test_validation_exception_with_nested_model(self, app, client):
        """Test validation exception with nested model."""

        class Address(BaseModel):
            street: str
            city: str

        class User(BaseModel):
            name: str
            address: Address

        @app.post("/test-validation-nested")
        def test_endpoint(data: User):
            return {"status": "ok"}

        response = client.post("/test-validation-nested", json={"name": "Test"})
        assert response.status_code == 422

        data = response.json()
        assert "errors" in data

    def test_database_exception_with_different_error(self, app, client):
        """Test database exception with different error types."""

        @app.get("/test-db-constraint")
        def test_endpoint():
            raise SQLAlchemyError("Constraint violation")

        response = client.get("/test-db-constraint")
        assert response.status_code == 500

        data = response.json()
        assert "detail" in data
        assert "database error" in data["detail"].lower()

    def test_general_exception_with_custom_error(self, app, client):
        """Test general exception with custom error."""

        class CustomError(Exception):
            pass

        @app.get("/test-custom-error")
        def test_endpoint():
            raise CustomError("Custom error message")

        response = client.get("/test-custom-error")
        assert response.status_code == 500

        data = response.json()
        assert "unexpected error" in data["detail"].lower()

    def test_http_exception_not_handled_by_handlers(self, app, client):
        """Test that HTTP exceptions are not caught by these handlers."""

        @app.get("/test-http")
        def test_endpoint():
            raise HTTPException(status_code=404, detail="Not found")

        response = client.get("/test-http")
        assert response.status_code == 404

    def test_validation_exception_timestamp_format(self, app, client):
        """Test validation exception timestamp format."""

        class TestModel(BaseModel):
            name: str

        @app.post("/test-timestamp")
        def test_endpoint(data: TestModel):
            return {"status": "ok"}

        response = client.post("/test-timestamp", json={})
        data = response.json()

        assert "timestamp" in data
        # Check ISO format without requiring Z suffix
        try:
            # Handle both with and without Z suffix
            timestamp = data["timestamp"]
            if timestamp.endswith("Z"):
                timestamp = timestamp.replace("Z", "+00:00")
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Timestamp is not in valid ISO format: {data['timestamp']}")

    def test_database_exception_timestamp_format(self, app, client):
        """Test database exception timestamp format."""

        @app.get("/test-db-timestamp")
        def test_endpoint():
            raise SQLAlchemyError("Error")

        response = client.get("/test-db-timestamp")
        data = response.json()

        assert "timestamp" in data
        # Check ISO format without requiring Z suffix
        try:
            timestamp = data["timestamp"]
            if timestamp.endswith("Z"):
                timestamp = timestamp.replace("Z", "+00:00")
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Timestamp is not in valid ISO format: {data['timestamp']}")