"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get database session as a context manager.

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()

    Automatically commits on success and rolls back on error.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """Get database session for dependency injection.

    Usage with FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Automatically closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database - create all tables.

    Note: In production, use Alembic migrations instead.
    This is mainly for development/testing.
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables.

    WARNING: This will delete all data!
    Only use in development/testing.
    """
    Base.metadata.drop_all(bind=engine)
