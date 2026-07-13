from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import SessionLocal
from config.logging_config import get_logger

logger = get_logger("database.health")


def check_database_connection(db: Optional[Session] = None, log = None) -> bool:
    """
    Check if the database connection is working.

    Args:
        db: Database session (optional)
        log: Optional logger for request-scoped logging

    Returns:
        True if connection succeeds, False otherwise.
    """
    try:
        if db is None:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
        else:
            db.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        if log:
            log.error(
                "Operational error connecting to database",
                error_type=type(e).__name__,
                error=str(e),
            )
        else:
            logger.error(
                "Operational error connecting to database",
                error_type=type(e).__name__,
                error=str(e),
            )
        return False
    except SQLAlchemyError as e:
        if log:
            log.error(
                "SQLAlchemy error connecting to database",
                error_type=type(e).__name__,
                error=str(e),
            )
        else:
            logger.error(
                "SQLAlchemy error connecting to database",
                error_type=type(e).__name__,
                error=str(e),
            )
        return False
    except Exception as e:
        if log:
            log.error(
                "Unexpected error connecting to database",
                error_type=type(e).__name__,
                error=str(e),
            )
        else:
            logger.error(
                "Unexpected error connecting to database",
                error_type=type(e).__name__,
                error=str(e),
            )
        return False


def get_database_status() -> dict:
    """
    Get detailed database status information.

    Returns:
        Dictionary with status and details.
    """
    try:
        with SessionLocal() as db:
            # Try to get PostgreSQL version
            try:
                result = db.execute(text("SELECT version()"))
                version_raw = result.scalar()
                version = version_raw.split(",")[0] if version_raw else "unknown"
            except Exception:
                # SQLite fallback
                result = db.execute(text("SELECT sqlite_version()"))
                version_raw = result.scalar()
                version = f"SQLite {version_raw}" if version_raw else "SQLite"

            # Try to get current database name
            try:
                result = db.execute(text("SELECT current_database()"))
                db_name = result.scalar()
            except Exception:
                # SQLite fallback
                db_name = "SQLite"

        return {
            "status": "healthy",
            "version": version,
            "database": db_name,
        }
    except OperationalError as e:
        return {
            "status": "unhealthy",
            "error": f"Connection failed: {str(e)}",
            "hint": "Check if database is running and credentials are correct",
        }
    except SQLAlchemyError as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }