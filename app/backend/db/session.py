"""SQLAlchemy engine/session bootstrap.

Scaffold only: provides the mechanics to open a SQLAlchemy engine/session
against a local SQLite file (via DATABASE_URL). No tables/models are declared
here yet; a future stage adds the actual schema (including the `sessions`
table anticipated for the opaque-session-token auth mechanism per DEC-005).
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

# check_same_thread=False is required for SQLite when used with FastAPI's
# threaded request handling; this is a standard SQLite+FastAPI pairing, not a
# business decision.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for future ORM models. No models defined yet."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
