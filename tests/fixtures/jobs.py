"""
Job-related fixtures for tests.
"""

from datetime import datetime

import pytest

from app.models import Job


@pytest.fixture
def sample_job_dict():
    """Sample job as dictionary."""
    return {
        "title": "Senior Python Developer",
        "company": "TechCorp Inc",
        "location": "San Francisco, CA",
        "description": "Looking for an experienced Python developer with FastAPI and PostgreSQL skills.",
        "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "salary_min": 120000,
        "salary_max": 180000,
        "posted_date": datetime.now().isoformat(),
        "source": "LinkedIn",
        "url": "https://linkedin.com/jobs/1",
        "is_active": True,
    }


@pytest.fixture
def sample_job_model(sample_job_dict):
    """Sample job as model instance."""
    return Job(**sample_job_dict)


@pytest.fixture
def multiple_job_dicts():
    """Multiple sample jobs as dictionaries."""
    return [
        {
            "title": "Senior Python Developer",
            "company": "TechCorp Inc",
            "location": "San Francisco, CA",
            "requirements": ["Python", "FastAPI"],
            "salary_min": 120000,
            "salary_max": 180000,
            "source": "LinkedIn",
        },
        {
            "title": "Data Engineer",
            "company": "DataInc",
            "location": "New York, NY",
            "requirements": ["Python", "Spark", "AWS"],
            "salary_min": 130000,
            "salary_max": 190000,
            "source": "Indeed",
        },
        {
            "title": "DevOps Engineer",
            "company": "CloudCo",
            "location": "Remote",
            "requirements": ["AWS", "Docker", "Kubernetes"],
            "salary_min": 110000,
            "salary_max": 170000,
            "source": "LinkedIn",
        },
    ]


@pytest.fixture
def job_with_extremes():
    """Job with extreme values for edge case testing."""
    return {
        "title": "Extreme Job",
        "company": "Extreme Corp",
        "location": "Antarctica",
        "requirements": ["Python"],
        "salary_min": 1,
        "salary_max": 1000000,
        "source": "Test",
        "description": "A" * 10000,  # Very long description
    }


@pytest.fixture
def invalid_job_data():
    """Invalid job data for validation testing."""
    return [
        {},  # Empty
        {"title": None, "company": "Test"},  # None title
        {"title": "Test", "company": ""},  # Empty company
        {"title": "Test", "company": "Test", "salary_min": -1000},  # Negative salary
        {
            "title": "Test",
            "company": "Test",
            "salary_min": 200000,
            "salary_max": 100000,
        },  # Min > Max
    ]
