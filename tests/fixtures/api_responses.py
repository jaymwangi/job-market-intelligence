"""
API response fixtures for testing.
"""

from datetime import datetime, timedelta

import pytest


@pytest.fixture
def api_health_response():
    """Mock API health check response."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {"database": "connected", "cache": "connected", "external_apis": "connected"},
    }


@pytest.fixture
def api_jobs_response(sample_jobs_data):
    """Mock API jobs list response."""
    return {
        "items": sample_jobs_data,
        "total": len(sample_jobs_data),
        "page": 1,
        "page_size": 20,
        "pages": 1,
    }


@pytest.fixture
def api_job_detail_response(sample_jobs_data):
    """Mock API job detail response."""
    return sample_jobs_data[0]


@pytest.fixture
def api_analytics_response(sample_analytics_data):
    """Mock API analytics response."""
    return {"success": True, "data": sample_analytics_data, "timestamp": datetime.now().isoformat()}


@pytest.fixture
def api_stats_response():
    """Mock API statistics response."""
    return {
        "total_jobs": 1500,
        "unique_skills": 45,
        "active_sources": 6,
        "jobs_updated_today": 125,
        "avg_salary_overall": 125000,
        "most_common_skill": "Python",
        "top_location": "San Francisco",
        "unique_companies": 320,
        "avg_jobs_per_company": 4.7,
    }


@pytest.fixture
def api_error_response():
    """Mock API error response."""
    return {
        "detail": "Resource not found",
        "status_code": 404,
        "error": "Not Found",
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def api_validation_error():
    """Mock API validation error response."""
    return {
        "detail": [
            {"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"}
        ],
        "status_code": 422,
    }


@pytest.fixture
def api_etl_response(mock_etl_results):
    """Mock API ETL trigger response."""
    return {
        "success": True,
        "message": "ETL pipeline triggered successfully",
        "run_id": mock_etl_results["run_id"],
        "status": "started",
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def api_etl_status_response():
    """Mock API ETL status response."""
    return {
        "run_id": "run_123",
        "status": "completed",
        "start_time": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "end_time": datetime.now().isoformat(),
        "records_processed": 100,
        "success_rate": 0.95,
        "errors": [],
    }


@pytest.fixture
def api_search_response(sample_jobs_data):
    """Mock API search response."""
    return {
        "items": sample_jobs_data[:2],
        "total": 2,
        "query": "Python",
        "filters": {"location": "San Francisco"},
        "page": 1,
        "page_size": 10,
    }


@pytest.fixture
def api_pagination_response():
    """Mock API pagination metadata."""
    return {
        "current_page": 2,
        "page_size": 20,
        "total_pages": 5,
        "total_items": 100,
        "has_next": True,
        "has_previous": True,
    }
