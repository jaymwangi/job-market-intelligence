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

from app.database.session import get_db
from app.main import app
from app.models import Job, PipelineRun, Skill


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a PostgreSQL engine for integration tests."""
    import os

    from dotenv import load_dotenv

    load_dotenv()

    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        raise RuntimeError("TEST_DATABASE_URL is not configured")

    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    try:
        # Verify the PostgreSQL test database is reachable.
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create an isolated PostgreSQL session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def api_client(db_session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client using the test database session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def sample_jobs_data() -> list[dict[str, Any]]:
    """Return sample job data for API and application tests."""
    return [
        {
            "id": 1,
            "title": "Senior Python Developer",
            "company_name": "TechCorp Inc",
            "location": "San Francisco, CA",
            "description": (
                "Looking for an experienced Python developer "
                "with FastAPI and PostgreSQL skills."
            ),
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
            "description": (
                "Build and maintain data pipelines using Python and Spark."
            ),
            "requirements": ["Python", "Spark", "AWS", "SQL"],
            "salary_min": 130000,
            "salary_max": 190000,
            "salary_currency": "USD",
            "posted_date": (
                datetime.now() - timedelta(days=5)
            ).isoformat(),
            "source_site": "Indeed",
            "source_url": "https://indeed.com/jobs/2",
            "is_active": True,
        },
        {
            "id": 3,
            "title": "DevOps Engineer",
            "company_name": "CloudCo",
            "location": "Remote",
            "description": (
                "Manage cloud infrastructure and CI/CD pipelines."
            ),
            "requirements": ["AWS", "Docker", "Kubernetes", "Terraform"],
            "salary_min": 110000,
            "salary_max": 170000,
            "salary_currency": "USD",
            "posted_date": (
                datetime.now() - timedelta(days=2)
            ).isoformat(),
            "source_site": "LinkedIn",
            "source_url": "https://linkedin.com/jobs/3",
            "is_active": True,
        },
    ]


@pytest.fixture
def create_test_jobs(db_session):
    """Create test Job records inside the current test transaction."""

    def _create_jobs(count: int = 5, **kwargs) -> list[Job]:
        jobs = []

        for i in range(count):
            job = Job(
                title=kwargs.get("title", f"Test Job {i}"),
                company_name=kwargs.get(
                    "company_name",
                    f"Test Company {i}",
                ),
                location=kwargs.get(
                    "location",
                    [
                        "San Francisco",
                        "New York",
                        "Remote",
                        "Austin",
                    ][i % 4],
                ),
                description=kwargs.get(
                    "description",
                    f"Test description for job {i}",
                ),
                salary_min=kwargs.get(
                    "salary_min",
                    100000 + (i * 10000),
                ),
                salary_max=kwargs.get(
                    "salary_max",
                    150000 + (i * 10000),
                ),
                salary_currency=kwargs.get(
                    "salary_currency",
                    "USD",
                ),
                source_site=kwargs.get(
                    "source_site",
                    "Test Source",
                ),
                source_id=kwargs.get(
                    "source_id",
                    f"test-source-id-{i}",
                ),
                source_url=kwargs.get(
                    "source_url",
                    f"https://test.com/jobs/{i}",
                ),
                posted_date=kwargs.get(
                    "posted_date",
                    datetime.now(),
                ),
                scraped_date=kwargs.get(
                    "scraped_date",
                    datetime.now(),
                ),
                is_active=kwargs.get(
                    "is_active",
                    True,
                ),
                is_deleted=kwargs.get(
                    "is_deleted",
                    False,
                ),
                language=kwargs.get(
                    "language",
                    "en",
                ),
                country_code=kwargs.get(
                    "country_code",
                    "US",
                ),
                employment_type=kwargs.get(
                    "employment_type",
                    "full-time",
                ),
                technology_category=kwargs.get(
                    "technology_category",
                    "backend",
                ),
                is_tech_role=kwargs.get(
                    "is_tech_role",
                    True,
                ),
            )

            db_session.add(job)
            jobs.append(job)

        # Flush instead of commit so the outer test transaction
        # remains active and can be rolled back by db_session.
        db_session.flush()

        return jobs

    return _create_jobs


@pytest.fixture
def create_test_skills(db_session):
    """Create test Skill records inside the current test transaction."""

    def _create_skills(skill_names: list[str] | None = None) -> list[Skill]:
        if skill_names is None:
            skill_names = [
                "Python",
                "JavaScript",
                "Java",
                "C++",
                "Go",
            ]

        skills = []

        for name in skill_names:
            skill = Skill(name=name)
            db_session.add(skill)
            skills.append(skill)

        # Flush to obtain generated IDs without committing.
        db_session.flush()

        return skills

    return _create_skills


@pytest.fixture
def create_test_pipeline_runs(db_session):
    """Create test PipelineRun records inside the current transaction."""

    def _create_runs(count: int = 5) -> list[PipelineRun]:
        runs = []

        for i in range(count):
            run = PipelineRun(
                status="completed" if i % 5 != 0 else "failed",
                started_at=datetime.now() - timedelta(days=i),
                completed_at=(
                    datetime.now()
                    - timedelta(days=i, hours=1)
                ),
                records_processed=100 + i * 10,
                source_site="test_source",
                duration_seconds=30 + i * 5,
                error_message="Error" if i % 5 == 0 else None,
            )

            db_session.add(run)
            runs.append(run)

        # Flush instead of commit to preserve transaction isolation.
        db_session.flush()

        return runs

    return _create_runs


@pytest.fixture
def sample_analytics_data() -> dict[str, Any]:
    """Return sample analytics data for testing."""
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
            "Python": {
                "min": 100000,
                "max": 180000,
                "avg": 135000,
            },
            "JavaScript": {
                "min": 90000,
                "max": 160000,
                "avg": 120000,
            },
            "Java": {
                "min": 95000,
                "max": 165000,
                "avg": 125000,
            },
            "C++": {
                "min": 105000,
                "max": 185000,
                "avg": 140000,
            },
        },
        "trends": {
            "dates": [
                (
                    datetime.now() - timedelta(days=i)
                ).strftime("%Y-%m-%d")
                for i in range(30, -1, -1)
            ],
            "counts": [
                100 + i * 10
                for i in range(31)
            ],
            "growth_rate": 0.15,
        },
        "pipeline_stats": {
            "total_jobs_processed": 1000,
            "successful_runs": 45,
            "failed_runs": 3,
            "avg_processing_time": 2.5,
        },
    }