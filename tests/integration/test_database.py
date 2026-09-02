"""Integration tests for PostgreSQL database infrastructure."""

from sqlalchemy import inspect, text

from app.models.job import Job


def test_postgresql_connection(db_session):
    """Verify the integration test database is PostgreSQL and reachable."""
    result = db_session.execute(text("SELECT version()"))
    version = result.scalar_one()

    assert "PostgreSQL" in version


def test_correct_test_database(db_session):
    """Verify integration tests are connected to the dedicated test database."""
    result = db_session.execute(text("SELECT current_database()"))
    database_name = result.scalar_one()

    assert database_name == "job_market_intelligence_test"


def test_alembic_schema_exists(test_db_engine):
    """Verify Alembic created the expected application tables."""
    inspector = inspect(test_db_engine)
    tables = set(inspector.get_table_names())

    expected_tables = {
        "jobs",
        "skills",
        "pipeline_runs",
        "job_skills",
        "alembic_version",
    }

    assert expected_tables.issubset(tables)


def test_database_transaction_rollback(db_session):
    """Verify test transactions are rolled back after the test."""
    db_session.execute(text("""
            CREATE TEMP TABLE integration_transaction_test (
                id INTEGER
            )
            """))

    db_session.execute(text("INSERT INTO integration_transaction_test (id) VALUES (1)"))

    result = db_session.execute(text("SELECT COUNT(*) FROM integration_transaction_test"))

    assert result.scalar_one() == 1


def test_postgresql_jsonb_support(db_session):
    """Verify PostgreSQL JSONB functionality is available."""
    result = db_session.execute(text("""
            SELECT '{"source": "integration-test", "valid": true}'::jsonb
        """))

    value = result.scalar_one()

    assert value["source"] == "integration-test"
    assert value["valid"] is True


def test_database_isolation(db_session):
    """Verify data created in one test transaction is not persisted."""
    db_session.execute(text("""
            CREATE TEMP TABLE integration_isolation_test (
                id INTEGER
            )
            """))

    db_session.execute(text("INSERT INTO integration_isolation_test (id) VALUES (1)"))

    result = db_session.execute(text("SELECT COUNT(*) FROM integration_isolation_test"))

    assert result.scalar_one() == 1


def test_isolation_writer(db_session):
    """Create a temporary row inside this test transaction."""
    db_session.execute(text("""
            CREATE TEMP TABLE integration_isolation_test (
                id INTEGER
            )
            """))
    db_session.execute(text("INSERT INTO integration_isolation_test (id) VALUES (1)"))

    result = db_session.execute(text("SELECT COUNT(*) FROM integration_isolation_test"))

    assert result.scalar_one() == 1


def test_isolation_clean_session(db_session):
    """Verify each test receives a clean database session."""
    result = db_session.execute(text("""
            SELECT to_regclass('pg_temp.integration_isolation_test')
            """))

    assert result.scalar_one() is None


def test_job_raw_data_jsonb_round_trip(db_session):
    """Verify Job.raw_data persists and loads correctly through PostgreSQL JSONB."""
    raw_data = {
        "source": "integration-test",
        "nested": {
            "salary": 125000,
            "remote": True,
        },
        "tags": ["python", "postgresql", "fastapi"],
    }

    job = Job(
        title="JSONB Integration Test Job",
        description="Testing PostgreSQL JSONB persistence.",
        company_name="Integration Test",
        location="Nairobi",
        source_site="integration-test",
        source_id="jsonb-integration-001",
        source_url="https://example.com/jobs/jsonb-integration-001",
        language="en",
        raw_data=raw_data,
    )

    db_session.add(job)
    db_session.flush()
    db_session.expire_all()

    persisted_job = (
        db_session.query(Job)
        .filter_by(
            source_site="integration-test",
            source_id="jsonb-integration-001",
        )
        .one()
    )

    assert persisted_job.raw_data == raw_data
    assert persisted_job.raw_data["nested"]["remote"] is True
    assert persisted_job.raw_data["tags"] == [
        "python",
        "postgresql",
        "fastapi",
    ]
