"""
Unit tests for dashboard analytics service error handling.
"""

from unittest.mock import Mock

import pytest

from dashboard.services.analytics_service import AnalyticsService


class TestAnalyticsServiceErrorHandling:
    """Test suite for analytics service error handling and edge cases."""

    @pytest.fixture
    def mock_api_client(self):
        """Mock API client."""
        mock = Mock()
        mock.get.return_value = {}
        return mock

    @pytest.fixture
    def mock_cache_manager(self):
        """Mock cache manager."""
        mock = Mock()
        mock.get.return_value = None
        return mock

    @pytest.fixture
    def service(self, mock_api_client, mock_cache_manager):
        """Create service instance."""
        return AnalyticsService(api_client=mock_api_client, cache_manager=mock_cache_manager)

    # ... (all other tests remain the same) ...

    def test_get_salary_statistics_with_none_response(self, service, mock_api_client):
        """Test getting salary statistics with None API response."""
        mock_api_client.get.return_value = None

        stats = service.get_salary_statistics()
        # Should return None when API returns None (error case)
        assert stats is None

    def test_get_salary_statistics_with_empty_response(self, service, mock_api_client):
        """Test getting salary statistics with empty API response."""
        mock_api_client.get.return_value = {}

        stats = service.get_salary_statistics()
        # Should handle gracefully - depends on implementation
        # The service may return None or a default SalaryStatistics
        assert stats is not None
