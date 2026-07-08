"""
Shared pytest fixtures and configuration for all tests.
"""

from collections.abc import Generator
from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.database.session import get_db

# Import from your actual modules
from app.main import app
from app.models import Job, PipelineRun, Skill


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create a test database engine using SQLite in memory.
    Note: SQLite doesn't support JSONB, so we use JSON instead.
    """
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, echo=False
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def api_client(db_session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Mark tests that require JSONB support as skipped
def pytest_collection_modifyitems(config, items):
    """Skip tests that require JSONB when using SQLite."""
    skip_jsonb = pytest.mark.skip(reason="JSONB not supported in SQLite")
    for item in items:
        # Skip tests in these modules
        if "test_loaders.py" in str(item.fspath):
            item.add_marker(skip_jsonb)
        elif "test_pipeline_repository.py" in str(item.fspath):
            item.add_marker(skip_jsonb)
        elif "test_skill_repository.py" in str(item.fspath):
            item.add_marker(skip_jsonb)
        elif "test_job_repository.py" in str(item.fspath):
            item.add_marker(skip_jsonb)


@pytest.fixture
def sample_jobs_data() -> list:
    """Sample job data for testing."""
    return [
        {
            "id": 1,
            "title": "Senior Python Developer",
            "company_name": "TechCorp Inc",
            "location": "San Francisco, CA",
            "description": "Looking for an experienced Python developer with FastAPI and PostgreSQL skills.",
            "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "salary_min": 120000,
            "salary_max": 180000,
            "salary_currency": "USD",
            "posted_date": datetime.now().isoformat(),
            "source_site": "LinkedIn",
            "source_url": "https://linkedin.com/jobs/1",
            "is_active": True,
        },
        {
            "id": 2,
            "title": "Data Engineer",
            "company_name": "DataInc",
            "location": "New York, NY",
            "description": "Build and maintain data pipelines using Python and Spark.",
            "requirements": ["Python", "Spark", "AWS", "SQL"],
            "salary_min": 130000,
            "salary_max": 190000,
            "salary_currency": "USD",
            "posted_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "source_site": "Indeed",
            "source_url": "https://indeed.com/jobs/2",
            "is_active": True,
        },
        {
            "id": 3,
            "title": "DevOps Engineer",
            "company_name": "CloudCo",
            "location": "Remote",
            "description": "Manage cloud infrastructure and CI/CD pipelines.",
            "requirements": ["AWS", "Docker", "Kubernetes", "Terraform"],
            "salary_min": 110000,
            "salary_max": 170000,
            "salary_currency": "USD",
            "posted_date": (datetime.now() - timedelta(days=2)).isoformat(),
            "source_site": "LinkedIn",
            "source_url": "https://linkedin.com/jobs/3",
            "is_active": True,
        },
    ]


@pytest.fixture
def create_test_jobs(db_session):
    """Create a set of test jobs in the database."""

    def _create_jobs(count=5, **kwargs):
        jobs = []
        for i in range(count):
            job = Job(
                title=kwargs.get("title", f"Test Job {i}"),
                company_name=kwargs.get("company_name", f"Test Company {i}"),
                location=kwargs.get(
                    "location", ["San Francisco", "New York", "Remote", "Austin"][i % 4]
                ),
                description=kwargs.get("description", f"Test description for job {i}"),
                requirements=kwargs.get("requirements", ["Python", "SQL", "Docker"][: (i % 3) + 1]),
                salary_min=kwargs.get("salary_min", 100000 + (i * 10000)),
                salary_max=kwargs.get("salary_max", 150000 + (i * 10000)),
                salary_currency=kwargs.get("salary_currency", "USD"),
                posted_date=kwargs.get("posted_date", datetime.now() - timedelta(days=i)),
                source_site=kwargs.get("source_site", "Test Source"),
                source_url=kwargs.get("source_url", f"https://test.com/jobs/{i}"),
                is_active=kwargs.get("is_active", True),
            )
            db_session.add(job)
            jobs.append(job)

        db_session.commit()

        for job in jobs:
            db_session.refresh(job)

        return jobs

    return _create_jobs


@pytest.fixture
def create_test_skills(db_session):
    """Create a set of test skills in the database."""

    def _create_skills(skill_names=None):
        if skill_names is None:
            skill_names = ["Python", "JavaScript", "Java", "C++", "Go"]

        skills = []
        for name in skill_names:
            skill = Skill(name=name, category="Programming Language")
            db_session.add(skill)
            skills.append(skill)

        db_session.commit()

        for skill in skills:
            db_session.refresh(skill)

        return skills

    return _create_skills


@pytest.fixture
def create_test_pipeline_runs(db_session):
    """Create a set of test pipeline runs in the database."""

    def _create_runs(count=5):
        runs = []
        for i in range(count):
            run = PipelineRun(
                status="completed" if i % 5 != 0 else "failed",
                started_at=datetime.now() - timedelta(days=i),
                completed_at=datetime.now() - timedelta(days=i, hours=1),
                records_processed=100 + i * 10,
                source_site="test_source",
                duration_seconds=30 + i * 5,
                error_message="Error" if i % 5 == 0 else None,
            )
            db_session.add(run)
            runs.append(run)

        db_session.commit()

        for run in runs:
            db_session.refresh(run)

        return runs

    return _create_runs


@pytest.fixture
def sample_analytics_data() -> dict[str, Any]:
    """Sample analytics data for testing."""
    return {
        "skill_distribution": {
            "Python": 450,
            "JavaScript": 380,
            "Java": 320,
            "C++": 180,
            "Go": 150,
        },
        "location_distribution": {
            "San Francisco": 200,
            "New York": 180,
            "Austin": 120,
            "Seattle": 100,
            "Boston": 90,
        },
        "salary_stats": {
            "Python": {"min": 100000, "max": 180000, "avg": 135000},
            "JavaScript": {"min": 90000, "max": 160000, "avg": 120000},
            "Java": {"min": 95000, "max": 165000, "avg": 125000},
            "C++": {"min": 105000, "max": 185000, "avg": 140000},
        },
        "trends": {
            "dates": [
                (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)
            ],
            "counts": [100 + i * 10 for i in range(31)],
            "growth_rate": 0.15,
        },
        "pipeline_stats": {
            "total_jobs_processed": 1000,
            "successful_runs": 45,
            "failed_runs": 3,
            "avg_processing_time": 2.5,
        },
    }
