import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class for ORM models."""


def _get_database_url() -> str:
    # Default to local SQLite, can be overridden by DATABASE_URL
    return os.getenv("DATABASE_URL", "sqlite:///./idea_kanban.db")


DATABASE_URL = _get_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Call once on application startup."""
    from src.adapters import models  # noqa: F401  - ensure models are imported

    Base.metadata.create_all(bind=engine)


