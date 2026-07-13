# app/database/session.py
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings


def _get_connect_args() -> dict[str, object]:
    """
    Get database-specific connection arguments.

    Returns:
        Dictionary of connect_args for the database engine.
    """
    # Use the sqlalchemy_database_url property from settings
    db_url = settings.sqlalchemy_database_url
    if db_url and db_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


# Get database URL from settings
database_url = settings.sqlalchemy_database_url

# Get pool settings from settings
pool_size = settings.db_pool_size
max_overflow = settings.db_max_overflow
debug = settings.debug
pool_timeout = settings.db_pool_timeout
pool_pre_ping = settings.db_pool_pre_ping

# Create database engine
engine = create_engine(
    database_url,
    echo=debug,  # Log SQL queries in debug mode
    pool_size=pool_size,  # Configurable pool size
    max_overflow=max_overflow,  # Configurable overflow
    pool_pre_ping=pool_pre_ping,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=pool_timeout,  # Timeout for getting connections from pool
    connect_args=_get_connect_args(),  # Database-specific connection args
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,  # Don't auto-flush before queries
    expire_on_commit=False,  # Don't expire objects after commit
)


def get_db() -> Generator[Session]:
    """
    Dependency for FastAPI to get database session.

    Yields:
        SQLAlchemy Session for use in request handlers.

    Ensures:
        - Session is closed after use
        - Transactions are rolled back on exceptions
        - Clean session state for each request

    Example:
        @app.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback transaction on any exception
        db.rollback()
        raise
    finally:
        # Always close the session
        db.close()


@contextmanager
def get_db_session() -> Generator[Session]:
    """
    Context manager for standalone database sessions (for use outside request context).

    Yields:
        SQLAlchemy Session for standalone use.

    Ensures:
        - Session is closed after use
        - Transactions are rolled back on exceptions

    Example:
        from app.database.session import get_db_session

        with get_db_session() as db:
            user = db.query(User).filter_by(id=1).first()
            # Session is automatically closed and rolled back on errors
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Module exports for cleaner imports
__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
]
