"""
Analytics-related fixtures for tests.
"""

from datetime import datetime, timedelta

import pytest

from app.models import Skill


@pytest.fixture
def sample_skill_distribution():
    """Sample skill distribution data."""
    return {
        "Python": 450,
        "JavaScript": 380,
        "Java": 320,
        "C++": 180,
        "Go": 150,
        "Rust": 90,
        "TypeScript": 200,
    }


@pytest.fixture
def sample_location_distribution():
    """Sample location distribution data."""
    return {
        "San Francisco": 200,
        "New York": 180,
        "Austin": 120,
        "Seattle": 100,
        "Boston": 90,
        "Remote": 250,
        "Chicago": 80,
    }


@pytest.fixture
def sample_salary_stats():
    """Sample salary statistics by skill."""
    return {
        "Python": {"min": 100000, "max": 180000, "avg": 135000, "median": 130000},
        "JavaScript": {"min": 90000, "max": 160000, "avg": 120000, "median": 115000},
        "Java": {"min": 95000, "max": 165000, "avg": 125000, "median": 120000},
        "C++": {"min": 105000, "max": 185000, "avg": 140000, "median": 135000},
        "Go": {"min": 110000, "max": 190000, "avg": 145000, "median": 140000},
    }


@pytest.fixture
def sample_trend_data():
    """Sample trend data for the last 30 days."""
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)]
    counts = [100 + i * 5 + (i % 3) * 2 for i in range(31)]

    return {
        "dates": dates,
        "counts": counts,
        "growth_rate": 0.15,
        "week_over_week": 0.12,
        "month_over_month": 0.08,
        "total_trend": counts[-1] - counts[0],
    }


@pytest.fixture
def sample_pipeline_stats():
    """Sample ETL pipeline statistics."""
    return {
        "total_jobs_processed": 5000,
        "successful_runs": 120,
        "failed_runs": 8,
        "avg_processing_time": 2.5,
        "total_processing_time": 300.0,
        "records_per_second": 16.67,
        "success_rate": 0.9375,
        "last_run_status": "completed",
        "last_run_time": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_skill_models():
    """Sample skill model instances."""
    skills = []
    skill_names = ["Python", "JavaScript", "Java", "C++", "Go", "Rust"]
    for name in skill_names:
        skill = Skill(name=name, category="Programming Language")
        skills.append(skill)
    return skills


@pytest.fixture
def sample_analytics_complete():
    """Complete analytics data payload."""
    return {
        "skill_distribution": {"Python": 450, "JavaScript": 380, "Java": 320},
        "location_distribution": {"San Francisco": 200, "New York": 180, "Remote": 150},
        "salary_stats": {
            "Python": {"min": 100000, "max": 180000, "avg": 135000},
            "JavaScript": {"min": 90000, "max": 160000, "avg": 120000},
        },
        "trends": {"dates": ["2026-01-01", "2026-01-02"], "counts": [100, 120]},
        "pipeline_stats": {"total_jobs_processed": 1000, "successful_runs": 45, "failed_runs": 3},
        "generated_at": datetime.now().isoformat(),
    }
