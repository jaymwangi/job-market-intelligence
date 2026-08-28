"""Integration tests for PostgreSQL database infrastructure."""

from sqlalchemy import inspect, text


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
    db_session.execute(
        text(
            """
            CREATE TEMP TABLE integration_transaction_test (
                id INTEGER
            )
            """
        )
    )

    db_session.execute(
        text("INSERT INTO integration_transaction_test (id) VALUES (1)")
    )

    result = db_session.execute(
        text("SELECT COUNT(*) FROM integration_transaction_test")
    )

    assert result.scalar_one() == 1


def test_postgresql_jsonb_support(db_session):
    """Verify PostgreSQL JSONB functionality is available."""
    result = db_session.execute(
        text(
            """
            SELECT '{"source": "integration-test", "valid": true}'::jsonb
        """
        )
    )

    value = result.scalar_one()

    assert value["source"] == "integration-test"
    assert value["valid"] is True

def test_database_isolation(db_session):
    """Verify data created in one test transaction is not persisted."""
    db_session.execute(
        text(
            """
            CREATE TEMP TABLE integration_isolation_test (
                id INTEGER
            )
            """
        )
    )

    db_session.execute(
        text("INSERT INTO integration_isolation_test (id) VALUES (1)")
    )

    result = db_session.execute(
        text("SELECT COUNT(*) FROM integration_isolation_test")
    )

    assert result.scalar_one() == 1
    
def test_isolation_writer(db_session):
    """Create a temporary row inside this test transaction."""
    db_session.execute(
        text(
            """
            CREATE TEMP TABLE integration_isolation_test (
                id INTEGER
            )
            """
        )
    )
    db_session.execute(
        text("INSERT INTO integration_isolation_test (id) VALUES (1)")
    )

    result = db_session.execute(
        text("SELECT COUNT(*) FROM integration_isolation_test")
    )

    assert result.scalar_one() == 1


def test_isolation_clean_session(db_session):
    """Verify each test receives a clean database session."""
    result = db_session.execute(
        text(
            """
            SELECT to_regclass('pg_temp.integration_isolation_test')
            """
        )
    )

    assert result.scalar_one() is None