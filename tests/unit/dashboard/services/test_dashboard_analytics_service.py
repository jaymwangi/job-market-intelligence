"""
Unit tests for dashboard analytics service error handling.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from schemas.analytics import DashboardSummary, SalaryStatistics

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

        # ============================================================

    # Sprint 6.6: Language Analytics
    # ============================================================

    @pytest.mark.parametrize(
        "method_name,endpoint",
        [
            (
                "get_language_distribution",
                "/api/v1/analytics/language/distribution",
            ),
            (
                "get_language_by_country",
                "/api/v1/analytics/language/by-country",
            ),
            (
                "get_language_salary_stats",
                "/api/v1/analytics/language/salary",
            ),
        ],
    )
    def test_language_list_methods_return_list_response(
        self,
        service,
        mock_api_client,
        method_name,
        endpoint,
    ):
        """List-based language methods return direct list responses."""
        expected = [{"language": "English", "count": 100}]
        mock_api_client.get.return_value = expected

        result = getattr(service, method_name)()

        assert result == expected
        mock_api_client.get.assert_called_once_with(endpoint)

    @pytest.mark.parametrize(
        "method_name,endpoint",
        [
            (
                "get_language_distribution",
                "/api/v1/analytics/language/distribution",
            ),
            (
                "get_language_by_country",
                "/api/v1/analytics/language/by-country",
            ),
            (
                "get_language_salary_stats",
                "/api/v1/analytics/language/salary",
            ),
        ],
    )
    def test_language_list_methods_unwrap_data_response(
        self,
        service,
        mock_api_client,
        method_name,
        endpoint,
    ):
        """List-based language methods unwrap data responses."""
        expected = [{"language": "English", "count": 100}]
        mock_api_client.get.return_value = {"data": expected}

        result = getattr(service, method_name)()

        assert result == expected
        mock_api_client.get.assert_called_once_with(endpoint)

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_language_distribution",
            "get_language_by_country",
            "get_language_salary_stats",
        ],
    )
    def test_language_list_methods_handle_invalid_response(
        self,
        service,
        mock_api_client,
        method_name,
    ):
        """List-based language methods return empty lists for invalid responses."""
        mock_api_client.get.return_value = {"unexpected": "value"}

        result = getattr(service, method_name)()

        assert result == []

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_language_distribution",
            "get_language_by_country",
            "get_language_salary_stats",
        ],
    )
    def test_language_list_methods_handle_api_errors(
        self,
        service,
        mock_api_client,
        method_name,
    ):
        """List-based language methods handle API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        result = getattr(service, method_name)()

        assert result == []

    def test_get_english_vs_non_english_returns_dict(
        self,
        service,
        mock_api_client,
    ):
        """English vs non-English returns a dictionary response."""
        expected = {
            "english_count": 80,
            "non_english_count": 20,
            "total_count": 100,
            "english_percentage": 80.0,
        }
        mock_api_client.get.return_value = expected

        result = service.get_english_vs_non_english()

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/language/english-vs-non-english"
        )

    def test_get_english_vs_non_english_handles_invalid_response(
        self,
        service,
        mock_api_client,
    ):
        """English vs non-English returns empty dict for invalid response."""
        mock_api_client.get.return_value = []

        assert service.get_english_vs_non_english() == {}

    def test_get_english_vs_non_english_handles_api_error(
        self,
        service,
        mock_api_client,
    ):
        """English vs non-English handles API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert service.get_english_vs_non_english() == {}

    # ============================================================
    # Sprint 6.6: Technology Analytics
    # ============================================================

    @pytest.mark.parametrize(
        "method_name,endpoint",
        [
            (
                "get_tech_category_distribution",
                "/api/v1/analytics/tech/category-distribution",
            ),
            (
                "get_tech_by_country",
                "/api/v1/analytics/tech/by-country",
            ),
        ],
    )
    def test_tech_list_methods_return_list_response(
        self,
        service,
        mock_api_client,
        method_name,
        endpoint,
    ):
        """List-based technology methods return direct list responses."""
        expected = [{"category": "Data", "count": 50}]
        mock_api_client.get.return_value = expected

        result = getattr(service, method_name)()

        assert result == expected
        mock_api_client.get.assert_called_once_with(endpoint)

    @pytest.mark.parametrize(
        "method_name,endpoint",
        [
            (
                "get_tech_category_distribution",
                "/api/v1/analytics/tech/category-distribution",
            ),
            (
                "get_tech_by_country",
                "/api/v1/analytics/tech/by-country",
            ),
        ],
    )
    def test_tech_list_methods_unwrap_data_response(
        self,
        service,
        mock_api_client,
        method_name,
        endpoint,
    ):
        """List-based technology methods unwrap data responses."""
        expected = [{"category": "Data", "count": 50}]
        mock_api_client.get.return_value = {"data": expected}

        result = getattr(service, method_name)()

        assert result == expected
        mock_api_client.get.assert_called_once_with(endpoint)

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_tech_category_distribution",
            "get_tech_by_country",
        ],
    )
    def test_tech_list_methods_handle_invalid_response(
        self,
        service,
        mock_api_client,
        method_name,
    ):
        """List-based technology methods handle invalid responses."""
        mock_api_client.get.return_value = {"unexpected": "value"}

        assert getattr(service, method_name)() == []

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_tech_category_distribution",
            "get_tech_by_country",
        ],
    )
    def test_tech_list_methods_handle_api_error(
        self,
        service,
        mock_api_client,
        method_name,
    ):
        """List-based technology methods handle API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert getattr(service, method_name)() == []

    def test_get_tech_vs_non_tech_returns_dict(
        self,
        service,
        mock_api_client,
    ):
        """Tech vs non-tech returns a dictionary response."""
        expected = {
            "tech_count": 70,
            "non_tech_count": 30,
            "total_count": 100,
            "tech_percentage": 70.0,
        }
        mock_api_client.get.return_value = expected

        result = service.get_tech_vs_non_tech()

        assert result == expected
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/tech/vs-non-tech")

    def test_get_tech_vs_non_tech_handles_invalid_response(
        self,
        service,
        mock_api_client,
    ):
        """Tech vs non-tech returns empty dict for invalid response."""
        mock_api_client.get.return_value = []

        assert service.get_tech_vs_non_tech() == {}

    def test_get_tech_vs_non_tech_handles_api_error(
        self,
        service,
        mock_api_client,
    ):
        """Tech vs non-tech handles API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert service.get_tech_vs_non_tech() == {}

    def test_get_tech_skills_passes_limit(
        self,
        service,
        mock_api_client,
    ):
        """Tech skills passes the requested limit."""
        expected = [{"skill": "Python", "count": 40}]
        mock_api_client.get.return_value = expected

        result = service.get_tech_skills(limit=25)

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/tech/skills",
            params={"limit": 25},
        )

    def test_get_tech_skills_unwraps_data_response(
        self,
        service,
        mock_api_client,
    ):
        """Tech skills unwraps a data response."""
        expected = [{"skill": "Python", "count": 40}]
        mock_api_client.get.return_value = {"data": expected}

        assert service.get_tech_skills() == expected

    def test_get_tech_skills_handles_invalid_response(
        self,
        service,
        mock_api_client,
    ):
        """Tech skills returns an empty list for invalid responses."""
        mock_api_client.get.return_value = {"unexpected": "value"}

        assert service.get_tech_skills() == []

    def test_get_tech_skills_handles_api_error(
        self,
        service,
        mock_api_client,
    ):
        """Tech skills handles API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert service.get_tech_skills() == []

    def test_get_tech_salary_stats_returns_dict(
        self,
        service,
        mock_api_client,
    ):
        """Tech salary statistics returns a dictionary."""
        expected = {
            "average": 75000,
            "min": 40000,
            "max": 120000,
            "median": 70000,
            "sample_size": 100,
        }
        mock_api_client.get.return_value = expected

        result = service.get_tech_salary_stats()

        assert result == expected
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/tech/salary")

    def test_get_tech_salary_stats_handles_invalid_response(
        self,
        service,
        mock_api_client,
    ):
        """Tech salary statistics handles invalid responses."""
        mock_api_client.get.return_value = []

        assert service.get_tech_salary_stats() == {}

    def test_get_tech_salary_stats_handles_api_error(
        self,
        service,
        mock_api_client,
    ):
        """Tech salary statistics handles API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert service.get_tech_salary_stats() == {}

    # ============================================================
    # Sprint 6.6: Enriched Analytics
    # ============================================================

    def test_get_enriched_top_skills_passes_filters(
        self,
        service,
        mock_api_client,
    ):
        """Enriched skills passes limit and optional filters."""
        expected = [{"skill": "Python", "count": 50}]
        mock_api_client.get.return_value = expected

        result = service.get_enriched_top_skills(
            limit=10,
            country_code="KE",
            tech_only=True,
        )

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/enriched/skills",
            params={
                "limit": "10",
                "country_code": "KE",
                "tech_only": "true",
            },
        )

    def test_get_enriched_top_skills_unwraps_data_response(
        self,
        service,
        mock_api_client,
    ):
        """Enriched skills unwraps a data response."""
        expected = [{"skill": "Python", "count": 50}]
        mock_api_client.get.return_value = {"data": expected}

        assert service.get_enriched_top_skills() == expected

    def test_get_enriched_top_skills_handles_invalid_response(
        self,
        service,
        mock_api_client,
    ):
        """Enriched skills handles invalid responses."""
        mock_api_client.get.return_value = {"unexpected": "value"}

        assert service.get_enriched_top_skills() == []

    def test_get_enriched_top_skills_handles_api_error(
        self,
        service,
        mock_api_client,
    ):
        """Enriched skills handles API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert service.get_enriched_top_skills() == []

    @pytest.mark.parametrize(
        "method_name,endpoint",
        [
            (
                "get_country_distribution",
                "/api/v1/analytics/enriched/countries",
            ),
            (
                "get_technology_distribution",
                "/api/v1/analytics/enriched/technology",
            ),
        ],
    )
    def test_enriched_list_methods_return_list_response(
        self,
        service,
        mock_api_client,
        method_name,
        endpoint,
    ):
        """Enriched list methods return direct list responses."""
        expected = [{"name": "Data", "count": 50}]
        mock_api_client.get.return_value = expected

        result = getattr(service, method_name)()

        assert result == expected
        mock_api_client.get.assert_called_once_with(endpoint)

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_country_distribution",
            "get_technology_distribution",
        ],
    )
    def test_enriched_list_methods_unwrap_data_response(
        self,
        service,
        mock_api_client,
        method_name,
    ):
        """Enriched list methods unwrap data responses."""
        expected = [{"name": "Data", "count": 50}]
        mock_api_client.get.return_value = {"data": expected}

        assert getattr(service, method_name)() == expected

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_country_distribution",
            "get_technology_distribution",
        ],
    )
    def test_enriched_list_methods_handle_invalid_response(
        self,
        service,
        mock_api_client,
        method_name,
    ):
        """Enriched list methods handle invalid responses."""
        mock_api_client.get.return_value = {"unexpected": "value"}

        assert getattr(service, method_name)() == []

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_country_distribution",
            "get_technology_distribution",
        ],
    )
    def test_enriched_list_methods_handle_api_error(
        self,
        service,
        mock_api_client,
        method_name,
    ):
        """Enriched list methods handle API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert getattr(service, method_name)() == []

    def test_get_enriched_salary_passes_filters(
        self,
        service,
        mock_api_client,
    ):
        """Enriched salary passes optional filters."""
        expected = {"average": 65000, "sample_size": 80}
        mock_api_client.get.return_value = expected

        result = service.get_enriched_salary(
            country_code="KE",
            tech_only=True,
        )

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/enriched/salary",
            params={
                "country_code": "KE",
                "tech_only": "true",
            },
        )

    def test_get_enriched_salary_returns_dict(
        self,
        service,
        mock_api_client,
    ):
        """Enriched salary returns dictionary responses."""
        expected = {"average": 65000, "sample_size": 80}
        mock_api_client.get.return_value = expected

        assert service.get_enriched_salary() == expected

    def test_get_enriched_salary_handles_invalid_response(
        self,
        service,
        mock_api_client,
    ):
        """Enriched salary returns empty dict for invalid responses."""
        mock_api_client.get.return_value = []

        assert service.get_enriched_salary() == {}

    def test_get_enriched_salary_handles_api_error(
        self,
        service,
        mock_api_client,
    ):
        """Enriched salary handles API failures."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert service.get_enriched_salary() == {}

    # ============================================================
    # ETL / Dashboard Status Methods
    # ============================================================

    def test_get_last_etl_run_returns_api_value(
        self,
        service,
        mock_api_client,
    ):
        """Last ETL run returns the API value when available."""
        mock_api_client.get.return_value = {"last_run": "2 hours ago"}

        result = service.get_last_etl_run()

        assert result == "2 hours ago"
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/etl/last-run")

    def test_get_last_etl_run_falls_back_when_api_has_no_value(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Last ETL run falls back when API provides no last_run."""
        mock_api_client.get.return_value = {}

        mock_repo = Mock()
        mock_repo.format_last_run_time.return_value = "1 day ago"

        mock_db = Mock()

        mock_get_db = Mock(return_value=iter([mock_db]))

        monkeypatch.setattr(
            "app.database.session.get_db",
            mock_get_db,
        )
        monkeypatch.setattr(
            "app.repositories.pipeline_run_repository.PipelineRunRepository",
            Mock(return_value=mock_repo),
        )

        result = service.get_last_etl_run()

        assert result == "1 day ago"
        mock_repo.format_last_run_time.assert_called_once()

    def test_get_last_etl_run_returns_na_on_fallback_error(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Last ETL run returns N/A when fallback also fails."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(side_effect=RuntimeError("DB unavailable")),
        )

        assert service.get_last_etl_run() == "N/A"

    def test_get_last_etl_run_handles_import_error(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Last ETL run returns N/A when app modules cannot be imported."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        import builtins

        original_import = builtins.__import__

        def raise_import_error(name, *args, **kwargs):
            if name == "app.database.session":
                raise ImportError("app modules unavailable")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", raise_import_error)

        assert service.get_last_etl_run() == "N/A"

    def test_get_last_etl_run_inserts_project_root(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Last ETL run adds project root to sys.path when missing."""
        mock_api_client.get.return_value = {}

        import os
        import sys

        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath("dashboard/services/analytics_service.py"))
            )
        )

        monkeypatch.setattr(
            sys,
            "path",
            [path for path in sys.path if path != project_root],
        )

        mock_repo = Mock()
        mock_repo.format_last_run_time.return_value = "1 day ago"

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(return_value=iter([Mock()])),
        )
        monkeypatch.setattr(
            "app.repositories.pipeline_run_repository.PipelineRunRepository",
            Mock(return_value=mock_repo),
        )

        assert service.get_last_etl_run() == "1 day ago"
        assert project_root in sys.path

    def test_get_last_etl_run_time_inserts_project_root(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Last ETL run time adds project root to sys.path when missing."""
        mock_api_client.get.return_value = {}

        import os
        import sys

        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath("dashboard/services/analytics_service.py"))
            )
        )

        monkeypatch.setattr(
            sys,
            "path",
            [path for path in sys.path if path != project_root],
        )

        expected = datetime(2026, 9, 10, 8, 30)

        mock_repo = Mock()
        mock_repo.get_last_run_time.return_value = expected

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(return_value=iter([Mock()])),
        )
        monkeypatch.setattr(
            "app.repositories.pipeline_run_repository.PipelineRunRepository",
            Mock(return_value=mock_repo),
        )

        assert service.get_last_etl_run_time() == expected
        assert project_root in sys.path

    def test_get_pipeline_status_inserts_project_root(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Pipeline status adds project root to sys.path when missing."""
        mock_api_client.get.return_value = {}

        import os
        import sys

        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath("dashboard/services/analytics_service.py"))
            )
        )

        monkeypatch.setattr(
            sys,
            "path",
            [path for path in sys.path if path != project_root],
        )

        mock_repo = Mock()
        mock_repo.get_running_run.return_value = None

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(return_value=iter([Mock()])),
        )
        monkeypatch.setattr(
            "app.repositories.pipeline_run_repository.PipelineRunRepository",
            Mock(return_value=mock_repo),
        )

        assert service.get_pipeline_status() == "Idle"
        assert project_root in sys.path

    def test_get_last_etl_run_time_returns_api_datetime(
        self,
        service,
        mock_api_client,
    ):
        """Last ETL run time converts the API timestamp to datetime."""
        timestamp = "2026-09-10T08:30:00"
        mock_api_client.get.return_value = {
            "last_run_time": timestamp,
        }

        result = service.get_last_etl_run_time()

        assert result == datetime.fromisoformat(timestamp)

    def test_get_last_etl_run_time_falls_back_to_repository(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Last ETL run time falls back to the repository."""
        mock_api_client.get.return_value = {}

        expected = datetime(2026, 9, 10, 8, 30)

        mock_repo = Mock()
        mock_repo.get_last_run_time.return_value = expected

        mock_db = Mock()

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(return_value=iter([mock_db])),
        )
        monkeypatch.setattr(
            "app.repositories.pipeline_run_repository.PipelineRunRepository",
            Mock(return_value=mock_repo),
        )

        result = service.get_last_etl_run_time()

        assert result == expected
        mock_repo.get_last_run_time.assert_called_once()

    def test_get_last_etl_run_time_returns_none_on_fallback_error(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Last ETL run time returns None when fallback fails."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(side_effect=RuntimeError("DB unavailable")),
        )

        assert service.get_last_etl_run_time() is None

    def test_get_pipeline_status_returns_api_status(
        self,
        service,
        mock_api_client,
    ):
        """Pipeline status returns the API status when available."""
        mock_api_client.get.return_value = {"status": "Running"}

        result = service.get_pipeline_status()

        assert result == "Running"
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/etl/status")

    @pytest.mark.parametrize(
        "running,expected",
        [
            (True, "Running"),
            (False, "Idle"),
        ],
    )
    def test_get_pipeline_status_falls_back_to_repository(
        self,
        service,
        mock_api_client,
        monkeypatch,
        running,
        expected,
    ):
        """Pipeline status derives Running/Idle from the repository."""
        mock_api_client.get.return_value = {}

        mock_repo = Mock()
        mock_repo.get_running_run.return_value = Mock() if running else None

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(return_value=iter([Mock()])),
        )
        monkeypatch.setattr(
            "app.repositories.pipeline_run_repository.PipelineRunRepository",
            Mock(return_value=mock_repo),
        )

        assert service.get_pipeline_status() == expected

    def test_get_pipeline_status_returns_unknown_on_fallback_error(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Pipeline status returns Unknown when fallback fails."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        monkeypatch.setattr(
            "app.database.session.get_db",
            Mock(side_effect=RuntimeError("DB unavailable")),
        )

        assert service.get_pipeline_status() == "Unknown"

    @pytest.mark.parametrize(
        "api_status,expected",
        [
            ({"status": "healthy"}, "Operational"),
            ({"status": "HEALTHY"}, "Operational"),
            ({"status": "ok"}, "Operational"),
            ({"status": "OK"}, "Operational"),
            ({"status": "unhealthy"}, "Degraded"),
            ({"status": "UNHEALTHY"}, "Degraded"),
            ({}, "Unknown"),
            (None, "Unknown"),
        ],
    )
    def test_get_db_status_maps_api_status(
        self,
        service,
        mock_api_client,
        api_status,
        expected,
    ):
        """Database API status maps to the dashboard status."""
        mock_api_client.get.return_value = api_status

        assert service.get_db_status() == expected

        mock_api_client.get.assert_called_once_with("/api/v1/health/db")

    def test_get_db_status_returns_unknown_on_api_error(
        self,
        service,
        mock_api_client,
    ):
        """Database status returns Unknown when the API fails."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        assert service.get_db_status() == "Unknown"

    def test_get_companies_hiring_count_returns_api_count(
        self,
        service,
        mock_api_client,
    ):
        """Companies hiring count returns the API count."""
        mock_api_client.get.return_value = {"count": 42}

        result = service.get_companies_hiring_count()

        assert result == 42
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/companies/count")

    def test_get_companies_hiring_count_falls_back_to_top_companies(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Companies hiring count falls back to top companies."""
        mock_api_client.get.return_value = {}

        companies = [Mock(), Mock(), Mock()]
        fetch_mock = Mock(return_value=companies)

        monkeypatch.setattr(
            service,
            "_fetch_top_companies",
            fetch_mock,
        )

        result = service.get_companies_hiring_count()

        assert result == 3
        fetch_mock.assert_called_once_with(limit=1000)

    def test_get_companies_hiring_count_returns_zero_on_fallback_error(
        self,
        service,
        mock_api_client,
        monkeypatch,
    ):
        """Companies hiring count returns zero when fallback fails."""
        mock_api_client.get.side_effect = RuntimeError("API unavailable")

        monkeypatch.setattr(
            service,
            "_fetch_top_companies",
            Mock(side_effect=RuntimeError("Repository unavailable")),
        )

        assert service.get_companies_hiring_count() == 0

    # ============================================================
    # Presentation / Chart Methods
    # ============================================================

    def test_get_dashboard_metrics_returns_mapped_result(
        self,
        service,
    ):
        """Dashboard metrics fetch data and pass it to the mapper."""
        summary = Mock()
        expected = [Mock()]

        service._fetch_dashboard_summary = Mock(return_value=summary)
        service.mapper.to_metric_cards = Mock(return_value=expected)

        result = service.get_dashboard_metrics()

        assert result == expected
        service._fetch_dashboard_summary.assert_called_once_with()
        service.mapper.to_metric_cards.assert_called_once_with(summary)

    def test_get_dashboard_metrics_returns_empty_list_on_error(
        self,
        service,
    ):
        """Dashboard metrics returns an empty list on failure."""
        service._fetch_dashboard_summary = Mock(side_effect=RuntimeError("fetch failed"))

        assert service.get_dashboard_metrics() == []

    def test_get_skills_chart_passes_limit_and_maps_result(
        self,
        service,
    ):
        """Skills chart passes the limit and maps the fetched skills."""
        skills = [Mock()]
        expected = Mock()

        service._fetch_top_skills = Mock(return_value=skills)
        service.mapper.to_horizontal_bar_chart = Mock(return_value=expected)

        result = service.get_skills_chart(limit=25)

        assert result == expected
        service._fetch_top_skills.assert_called_once_with(25)

        kwargs = service.mapper.to_horizontal_bar_chart.call_args.kwargs
        assert kwargs["data"] == skills
        assert kwargs["title"] == "Most In-Demand Skills"
        assert kwargs["label_field"] == "skill"
        assert kwargs["value_field"] == "count"
        assert kwargs["x_label"] == "Job Count"
        assert kwargs["y_label"] == "Skill"
        assert kwargs["show_values"] is True

    def test_get_skills_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Skills chart returns an empty chart on failure."""
        service._fetch_top_skills = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_skills_chart()

        assert result.title == "Most In-Demand Skills"
        assert result.x_values == []
        assert result.y_values == []

    def test_get_skills_distribution_chart_maps_result(
        self,
        service,
    ):
        """Skills distribution uses the pie-chart mapper."""
        skills = [Mock()]
        expected = Mock()

        service._fetch_top_skills = Mock(return_value=skills)
        service.mapper.to_pie_chart = Mock(return_value=expected)

        result = service.get_skills_distribution_chart(limit=12)

        assert result == expected
        service._fetch_top_skills.assert_called_once_with(12)

        kwargs = service.mapper.to_pie_chart.call_args.kwargs
        assert kwargs["data"] == skills
        assert kwargs["title"] == "Skill Distribution"
        assert kwargs["label_field"] == "skill"
        assert kwargs["value_field"] == "count"
        assert kwargs["show_percentage"] is True

    def test_get_skills_distribution_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Skills distribution returns an empty chart on failure."""
        service._fetch_top_skills = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_skills_distribution_chart()

        assert result.title == "Skill Distribution"
        assert result.labels == []
        assert result.values == []

    def test_get_companies_chart_passes_limit_and_maps_result(
        self,
        service,
    ):
        """Companies chart fetches and maps companies."""
        companies = [Mock()]
        expected = Mock()

        service._fetch_top_companies = Mock(return_value=companies)
        service.mapper.to_horizontal_bar_chart = Mock(return_value=expected)

        result = service.get_companies_chart(limit=20)

        assert result == expected
        service._fetch_top_companies.assert_called_once_with(20)

        kwargs = service.mapper.to_horizontal_bar_chart.call_args.kwargs
        assert kwargs["data"] == companies
        assert kwargs["title"] == "Top Companies by Job Postings"
        assert kwargs["label_field"] == "company"
        assert kwargs["value_field"] == "job_count"
        assert kwargs["show_values"] is True

    def test_get_companies_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Companies chart returns an empty chart on failure."""
        service._fetch_top_companies = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_companies_chart()

        assert result.title == "Top Companies by Job Postings"
        assert result.x_values == []
        assert result.y_values == []

    def test_get_companies_distribution_chart_maps_result(
        self,
        service,
    ):
        """Companies distribution uses the donut mapper."""
        companies = [Mock()]
        expected = Mock()

        service._fetch_top_companies = Mock(return_value=companies)
        service.mapper.to_donut_chart = Mock(return_value=expected)

        result = service.get_companies_distribution_chart(limit=12)

        assert result == expected
        service._fetch_top_companies.assert_called_once_with(12)

        kwargs = service.mapper.to_donut_chart.call_args.kwargs
        assert kwargs["data"] == companies
        assert kwargs["title"] == "Company Distribution"
        assert kwargs["label_field"] == "company"
        assert kwargs["value_field"] == "job_count"
        assert kwargs["show_percentage"] is True
        assert kwargs["hole_size"] == 0.4

    def test_get_companies_distribution_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Companies distribution returns an empty chart on failure."""
        service._fetch_top_companies = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_companies_distribution_chart()

        assert result.title == "Company Distribution"
        assert result.labels == []
        assert result.values == []

    def test_get_locations_chart_passes_limit_and_maps_result(
        self,
        service,
    ):
        """Locations chart fetches and maps locations."""
        locations = [Mock()]
        expected = Mock()

        service._fetch_jobs_by_location = Mock(return_value=locations)
        service.mapper.to_horizontal_bar_chart = Mock(return_value=expected)

        result = service.get_locations_chart(limit=20)

        assert result == expected
        service._fetch_jobs_by_location.assert_called_once_with(20)

        kwargs = service.mapper.to_horizontal_bar_chart.call_args.kwargs
        assert kwargs["data"] == locations
        assert kwargs["title"] == "Top Locations by Job Count"
        assert kwargs["label_field"] == "location"
        assert kwargs["value_field"] == "job_count"
        assert kwargs["show_values"] is True

    def test_get_locations_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Locations chart returns an empty chart on failure."""
        service._fetch_jobs_by_location = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_locations_chart()

        assert result.title == "Top Locations by Job Count"
        assert result.x_values == []
        assert result.y_values == []

    def test_get_salary_distribution_chart_maps_result(
        self,
        service,
    ):
        """Salary distribution uses the histogram mapper."""
        distribution = [Mock()]
        expected = Mock()

        service._fetch_salary_distribution = Mock(return_value=distribution)
        service.mapper.to_salary_histogram = Mock(return_value=expected)

        result = service.get_salary_distribution_chart()

        assert result == expected
        service._fetch_salary_distribution.assert_called_once_with()
        service.mapper.to_salary_histogram.assert_called_once_with(distribution)

    def test_get_salary_distribution_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Salary distribution returns an empty histogram on failure."""
        service._fetch_salary_distribution = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_salary_distribution_chart()

        assert result.title == "Salary Distribution"
        assert result.bins == []
        assert result.counts == []

    def test_get_salary_by_location_chart_passes_limit_and_maps_result(
        self,
        service,
    ):
        """Salary by location passes the limit to the fetcher."""
        salary_locations = [Mock()]
        expected = Mock()

        service._fetch_salary_by_location = Mock(return_value=salary_locations)
        service.mapper.to_bar_chart = Mock(return_value=expected)

        result = service.get_salary_by_location_chart(limit=15)

        assert result == expected
        service._fetch_salary_by_location.assert_called_once_with(15)

        kwargs = service.mapper.to_bar_chart.call_args.kwargs
        assert kwargs["data"] == salary_locations
        assert kwargs["title"] == "Average Salary by Location"
        assert kwargs["label_field"] == "location"
        assert kwargs["value_field"] == "average_salary"
        assert kwargs["show_values"] is True

    def test_get_salary_by_location_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Salary by location returns an empty chart on failure."""
        service._fetch_salary_by_location = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_salary_by_location_chart()

        assert result.title == "Average Salary by Location"
        assert result.x_values == []
        assert result.y_values == []

    def test_get_employment_types_chart_maps_result(
        self,
        service,
    ):
        """Employment types chart uses the donut mapper."""
        employment_types = [Mock()]
        expected = Mock()

        service._fetch_employment_types = Mock(return_value=employment_types)
        service.mapper.to_donut_chart = Mock(return_value=expected)

        result = service.get_employment_types_chart()

        assert result == expected
        service._fetch_employment_types.assert_called_once_with()

        kwargs = service.mapper.to_donut_chart.call_args.kwargs
        assert kwargs["data"] == employment_types
        assert kwargs["title"] == "Employment Type Distribution"
        assert kwargs["label_field"] == "employment_type"
        assert kwargs["value_field"] == "count"
        assert kwargs["show_percentage"] is True
        assert kwargs["hole_size"] == 0.4

    def test_get_employment_types_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Employment types chart returns an empty chart on failure."""
        service._fetch_employment_types = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_employment_types_chart()

        assert result.title == "Employment Type Distribution"
        assert result.labels == []
        assert result.values == []

    def test_get_employment_types_bar_chart_maps_result(
        self,
        service,
    ):
        """Employment types bar chart uses the bar mapper."""
        employment_types = [Mock()]
        expected = Mock()

        service._fetch_employment_types = Mock(return_value=employment_types)
        service.mapper.to_bar_chart = Mock(return_value=expected)

        result = service.get_employment_types_bar_chart()

        assert result == expected
        service._fetch_employment_types.assert_called_once_with()

        kwargs = service.mapper.to_bar_chart.call_args.kwargs
        assert kwargs["data"] == employment_types
        assert kwargs["title"] == "Employment Type Counts"
        assert kwargs["label_field"] == "employment_type"
        assert kwargs["value_field"] == "count"
        assert kwargs["show_values"] is True

    def test_get_employment_types_bar_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Employment types bar chart returns an empty chart on failure."""
        service._fetch_employment_types = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_employment_types_bar_chart()

        assert result.title == "Employment Type Counts"
        assert result.x_values == []
        assert result.y_values == []

    def test_get_posting_trend_chart_passes_days_and_maps_result(
        self,
        service,
    ):
        """Posting trend chart passes days and uses cumulative values."""
        trends = [Mock()]
        expected = Mock()

        service._fetch_posting_trend = Mock(return_value=trends)
        service.mapper.to_line_chart = Mock(return_value=expected)

        result = service.get_posting_trend_chart(days=45)

        assert result == expected
        service._fetch_posting_trend.assert_called_once_with(45)

        kwargs = service.mapper.to_line_chart.call_args.kwargs
        assert kwargs["data"] == trends
        assert kwargs["title"] == "Job Postings Over Time (Last 45 Days)"
        assert kwargs["x_field"] == "date"
        assert kwargs["y_field"] == "cumulative"
        assert kwargs["fill_area"] is True
        assert kwargs["show_markers"] is True

    def test_get_posting_trend_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Posting trend returns an empty chart on failure."""
        service._fetch_posting_trend = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_posting_trend_chart()

        assert result.title == "Job Postings Over Time"
        assert result.x_values == []
        assert result.y_values == []

    def test_get_daily_posting_trend_chart_passes_days_and_maps_result(
        self,
        service,
    ):
        """Daily posting trend passes days and uses daily counts."""
        trends = [Mock()]
        expected = Mock()

        service._fetch_posting_trend = Mock(return_value=trends)
        service.mapper.to_line_chart = Mock(return_value=expected)

        result = service.get_daily_posting_trend_chart(days=45)

        assert result == expected
        service._fetch_posting_trend.assert_called_once_with(45)

        kwargs = service.mapper.to_line_chart.call_args.kwargs
        assert kwargs["data"] == trends
        assert kwargs["title"] == "Daily Job Postings"
        assert kwargs["x_field"] == "date"
        assert kwargs["y_field"] == "count"
        assert kwargs["fill_area"] is False
        assert kwargs["show_markers"] is True

    def test_get_daily_posting_trend_chart_returns_empty_chart_on_error(
        self,
        service,
    ):
        """Daily posting trend returns an empty chart on failure."""
        service._fetch_posting_trend = Mock(side_effect=RuntimeError("fetch failed"))

        result = service.get_daily_posting_trend_chart()

        assert result.title == "Daily Job Postings"
        assert result.x_values == []
        assert result.y_values == []
        # ============================================================

    # Private fetch / normalization methods
    # ============================================================

    def test_fetch_dashboard_summary_normalizes_response(self, service, mock_api_client):
        data = {"total_jobs": 10}
        expected = Mock()
        service._normalize_response = Mock(return_value=expected)
        mock_api_client.get.return_value = data

        result = service._fetch_dashboard_summary()

        assert result is expected
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/dashboard-summary")
        service._normalize_response.assert_called_once()
        assert service._normalize_response.call_args.args[0] == data
        assert service._normalize_response.call_args.args[1] is DashboardSummary

    def test_fetch_top_skills_normalizes_list(self, service, mock_api_client):
        data = [{"skill": "Python", "count": 10}]
        expected = [Mock()]
        service._normalize_list = Mock(return_value=expected)
        mock_api_client.get.return_value = data

        result = service._fetch_top_skills(25)

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/top-skills",
            params={"limit": 25},
        )
        service._normalize_list.assert_called_once()

    def test_fetch_top_companies_normalizes_list(self, service, mock_api_client):
        expected = [Mock()]
        service._normalize_list = Mock(return_value=expected)

        result = service._fetch_top_companies(20)

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/top-companies",
            params={"limit": 20},
        )
        service._normalize_list.assert_called_once()

    def test_fetch_jobs_by_location_normalizes_list(self, service, mock_api_client):
        expected = [Mock()]
        service._normalize_list = Mock(return_value=expected)

        result = service._fetch_jobs_by_location(15)

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/jobs-by-location",
            params={"limit": 15},
        )
        service._normalize_list.assert_called_once()

    def test_fetch_salary_statistics_normalizes_response(self, service, mock_api_client):
        expected = Mock()
        service._normalize_response = Mock(return_value=expected)

        result = service._fetch_salary_statistics()

        assert result is expected
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/salary-statistics")
        service._normalize_response.assert_called_once()

    def test_fetch_salary_distribution_normalizes_list(self, service, mock_api_client):
        expected = [Mock()]
        service._normalize_list = Mock(return_value=expected)

        result = service._fetch_salary_distribution()

        assert result == expected
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/salary-distribution")
        service._normalize_list.assert_called_once()

    def test_fetch_salary_by_location_normalizes_list(self, service, mock_api_client):
        expected = [Mock()]
        service._normalize_list = Mock(return_value=expected)

        result = service._fetch_salary_by_location(10)

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/salary-by-location",
            params={"limit": 10},
        )
        service._normalize_list.assert_called_once()

    def test_fetch_employment_types_normalizes_list(self, service, mock_api_client):
        expected = [Mock()]
        service._normalize_list = Mock(return_value=expected)

        result = service._fetch_employment_types()

        assert result == expected
        mock_api_client.get.assert_called_once_with("/api/v1/analytics/employment-types")
        service._normalize_list.assert_called_once()

    def test_fetch_posting_trend_normalizes_list(self, service, mock_api_client):
        expected = [Mock()]
        service._normalize_list = Mock(return_value=expected)

        result = service._fetch_posting_trend(30)

        assert result == expected
        mock_api_client.get.assert_called_once_with(
            "/api/v1/analytics/posting-trend",
            params={"days": 30},
        )
        service._normalize_list.assert_called_once()

    def test_normalize_dashboard_summary_missing_salary_statistics(self, service):
        data = {
            "total_jobs": 10,
            "recent_jobs_count": 5,
            "top_companies": [],
            "top_locations": [],
            "top_skills": [],
            "employment_types": [],
            "posting_trend": [],
        }

        result = service._normalize_response(data, DashboardSummary)

        stats = result.salary_statistics
        assert stats.average == 0
        assert stats.minimum == 0
        assert stats.maximum == 0
        assert stats.median == 0
        assert stats.sample_size == 0
        assert stats.currency == "USD"

    def test_normalize_dashboard_summary_none_salary_statistics(self, service):
        data = {
            "total_jobs": 10,
            "recent_jobs_count": 5,
            "top_companies": [],
            "top_locations": [],
            "top_skills": [],
            "employment_types": [],
            "posting_trend": [],
            "salary_statistics": None,
        }

        result = service._normalize_response(data, DashboardSummary)

        stats = result.salary_statistics
        assert stats.average == 0
        assert stats.minimum == 0
        assert stats.maximum == 0
        assert stats.median == 0
        assert stats.sample_size == 0
        assert stats.currency == "USD"

    def test_normalize_dashboard_summary_none_salary_fields(self, service):
        data = {
            "total_jobs": 10,
            "recent_jobs_count": 5,
            "top_companies": [],
            "top_locations": [],
            "top_skills": [],
            "employment_types": [],
            "posting_trend": [],
            "salary_statistics": {
                "average": None,
                "minimum": None,
                "maximum": None,
                "median": None,
                "sample_size": None,
                "currency": None,
            },
        }

        result = service._normalize_response(data, DashboardSummary)

        stats = result.salary_statistics
        assert stats.average == 0
        assert stats.minimum == 0
        assert stats.maximum == 0
        assert stats.median == 0
        assert stats.sample_size == 0
        assert stats.currency == "USD"

    def test_normalize_salary_statistics_none_fields(self, service):
        data = {
            "average": None,
            "minimum": None,
            "maximum": None,
            "median": None,
            "sample_size": None,
            "currency": None,
        }

        result = service._normalize_response(data, SalaryStatistics)

        assert result.average == 0
        assert result.minimum == 0
        assert result.maximum == 0
        assert result.median == 0
        assert result.sample_size == 0
        assert result.currency == "USD"

    def test_normalize_response_invalid_data_returns_empty_model(self, service):
        result = service._normalize_response(
            {"unexpected": object()},
            SalaryStatistics,
        )

        assert isinstance(result, SalaryStatistics)

    def test_normalize_response_invalid_data_raises_when_fallback_fails(self, service):
        class BrokenModel:
            def __init__(self, **kwargs):
                raise RuntimeError("cannot construct")

        with pytest.raises(ValueError, match="Invalid response format"):
            service._normalize_response({"bad": True}, BrokenModel)

    def test_normalize_list_normalizes_each_item(self, service):
        items = [{"a": 1}, {"a": 2}]
        expected = [Mock(), Mock()]
        service._normalize_response = Mock(side_effect=expected)

        result = service._normalize_list(items, SalaryStatistics)

        assert result == expected
        assert service._normalize_response.call_count == 2

    def test_refresh_all_clears_cache(self, service, mock_cache_manager):
        service.refresh_all()

        mock_cache_manager.clear.assert_called_once()
