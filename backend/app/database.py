"""
Database configuration and session management for the Amendment System.

This module provides:
- SQLAlchemy engine configuration with proper error handling
- Database session management
- Base model class with common audit fields
- Database connection utilities
"""

from typing import Generator
import os
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    Base class for all database models.

    All models should inherit from this class to automatically
    include SQLAlchemy metadata and common functionality.
    """

    pass


# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./amendment_system.db")

# Validate DATABASE_URL format
if not DATABASE_URL or DATABASE_URL.strip() == "":
    raise ValueError("DATABASE_URL environment variable must be set and non-empty")

# Database engine configuration
try:
    # Determine if we're using SQLite
    is_sqlite = DATABASE_URL.startswith("sqlite")

    # Configure engine with appropriate settings
    if is_sqlite:
        # SQLite-specific configuration
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=pool.StaticPool,  # Better for SQLite
            echo=os.getenv("SQL_ECHO", "False").lower() == "true",
        )

        # Enable foreign key constraints for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info(f"SQLite database engine created: {DATABASE_URL}")
    else:
        # PostgreSQL/MySQL configuration
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
            echo=os.getenv("SQL_ECHO", "False").lower() == "true",
        )
        db_name = (
            DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "database"
        )
        logger.info(f"Database engine created for: {db_name}")

except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise RuntimeError(f"Database engine creation failed: {e}") from e


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Prevent issues with detached instances
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        with get_db_context() as db:
            db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This function should be called on application startup.
    It creates all tables defined in the models that inherit from Base.

    Raises:
        RuntimeError: If database initialization fails
    """
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except OperationalError as e:
        logger.error(f"Database connection failed during initialization: {e}")
        raise RuntimeError(f"Could not connect to database: {e}") from e
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise RuntimeError(f"Database initialization failed: {e}") from e


def check_db_connection() -> bool:
    """
    Check if the database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection check: OK")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def drop_all_tables() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    Should only be used in development/testing.
    """
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise RuntimeError("Cannot drop tables in production environment!")

    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped successfully")


def reset_db() -> None:
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data!
    Should only be used in development/testing.
    """
    drop_all_tables()
    init_db()
