# database/health.py
import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.database.session import engine

logger = logging.getLogger(__name__)


def check_database_connection() -> bool:
    """
    Check if the database connection is working.

    Returns:
        True if connection succeeds, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        logger.error(f"Operational error connecting to database: {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error connecting to database: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error connecting to database: {e}")
        return False


def get_database_status() -> dict:
    """
    Get detailed database status information.

    Returns:
        Dictionary with status and details.
    """
    try:
        with engine.connect() as connection:
            # Get PostgreSQL version
            result = connection.execute(text("SELECT version()"))
            version: str | None = result.scalar()

            # Get current database name
            result = connection.execute(text("SELECT current_database()"))
            db_name: str | None = result.scalar()

        return {
            "status": "healthy",
            "version": version.split(",")[0] if version else "unknown",
            "database": db_name if db_name else "unknown",
        }
    except OperationalError as e:
        return {
            "status": "unhealthy",
            "error": f"Connection failed: {str(e)}",
            "hint": "Check if PostgreSQL is running and credentials are correct",
        }
    except SQLAlchemyError as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
