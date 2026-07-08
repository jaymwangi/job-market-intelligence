"""
Unit tests for dashboard health service.
"""

from unittest.mock import Mock

import pytest

from dashboard.schemas.health import HealthResponse
from dashboard.services.health import HealthService


class TestHealthService:
    """Test suite for health service."""

    @pytest.fixture
    def mock_api_client(self):
        """Mock API client."""
        mock = Mock()
        mock.get.return_value = {"status": "healthy", "database": "connected"}
        return mock

    @pytest.fixture
    def service(self, mock_api_client):
        """Create service instance."""
        return HealthService(api_client=mock_api_client, cache_manager=None)

    def test_check_healthy(self, service, mock_api_client):
        """Test health check when API is healthy."""
        result = service.check()

        assert isinstance(result, HealthResponse)
        assert result.status == "healthy"
        mock_api_client.get.assert_called_once()

    def test_check_unhealthy(self, service, mock_api_client):
        """Test health check when API is unhealthy."""
        mock_api_client.get.return_value = {"status": "unhealthy", "database": "disconnected"}

        result = service.check()
        assert result.status == "unhealthy"

    def test_check_api_error(self, service, mock_api_client):
        """Test health check when API request fails."""
        mock_api_client.get.side_effect = Exception("API Error")

        result = service.check()
        assert result.status == "unhealthy"

    def test_is_healthy_true(self, service, mock_api_client):
        """Test is_healthy when API is healthy."""
        mock_api_client.get.return_value = {"status": "healthy"}

        result = service.is_healthy()
        assert result is True

    def test_is_healthy_false(self, service, mock_api_client):
        """Test is_healthy when API is unhealthy."""
        mock_api_client.get.return_value = {"status": "unhealthy"}

        result = service.is_healthy()
        assert result is False

    def test_is_healthy_api_error(self, service, mock_api_client):
        """Test is_healthy when API request fails."""
        mock_api_client.get.side_effect = Exception("API Error")

        result = service.is_healthy()
        assert result is False
