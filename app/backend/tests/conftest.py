"""Pytest fixtures for the ACRI-66 auth test suite.

Provides an isolated, per-test SQLite database (a fresh temp file — Q1 in
the implementation plan: temp-file, not the developer's local `app.db`), a
`TestClient` wired to it via FastAPI dependency override, and a helper to
seed known test users. This helper is deliberately decoupled from the
env-configured demo-account seed script (`db.seed.seed_demo_accounts`),
which has its own dedicated tests in `test_seed_demo_accounts.py`.

`DATABASE_URL` (and the `SEED_*` env vars) are set at module import time,
before `main`/`db.session` are ever imported by any test module, so that
even if the app's own startup lifespan runs it never touches the real
developer `app.db` file.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator, Iterator

# Must happen before `main`/`db.session` is imported by any test module.
_GLOBAL_TEST_DB_FD, _GLOBAL_TEST_DB_PATH = tempfile.mkstemp(suffix="_global_test_app.db")
os.close(_GLOBAL_TEST_DB_FD)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_GLOBAL_TEST_DB_PATH}")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")
os.environ.setdefault("SEED_KITCHEN_MANAGER_EMAIL", "test.kitchen.manager@example.com")
os.environ.setdefault("SEED_KITCHEN_MANAGER_PASSWORD", "test-only-kitchen-manager-pw")
os.environ.setdefault("SEED_FB_MANAGER_EMAIL", "test.fb.manager@example.com")
os.environ.setdefault("SEED_FB_MANAGER_PASSWORD", "test-only-fb-manager-pw")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from db.models import Persona, User  # noqa: E402
from db.session import Base, get_db  # noqa: E402
from services.auth_service import hash_password  # noqa: E402

KITCHEN_MANAGER_EMAIL = "kitchen.manager.test@example.com"
KITCHEN_MANAGER_PASSWORD = "correct-horse-battery-staple-km"
FB_MANAGER_EMAIL = "fb.manager.test@example.com"
FB_MANAGER_PASSWORD = "correct-horse-battery-staple-fb"


@pytest.fixture()
def test_engine() -> Iterator[Engine]:
    """A fresh temp-file SQLite database, isolated per test."""
    fd, path = tempfile.mkstemp(suffix="_test.db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()
        os.remove(path)


@pytest.fixture()
def db_session_factory(test_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session(db_session_factory: sessionmaker[Session]) -> Iterator[Session]:
    db = db_session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """A `TestClient` whose `get_db` dependency is overridden to use the
    isolated per-test database. Intentionally not used as a context manager
    (`with TestClient(...)`) so the app's real startup lifespan — which
    would touch the *global* engine/`SEED_*` accounts — never fires for
    these route-level tests; each test seeds only the specific users it
    needs via `seed_known_users`/`seed_user`.
    """
    from main import app

    def _override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def seed_user(db: Session, *, email: str, password: str, persona: str) -> User:
    """Create and persist a single known test user."""
    user = User(email=email.strip().lower(), password_hash=hash_password(password), persona=persona)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_known_users(db: Session) -> tuple[User, User]:
    """Seed exactly the 2 documented-shape test personas (AC4) with known,
    distinct credentials, and return (kitchen_manager, fb_manager)."""
    kitchen_manager = seed_user(
        db,
        email=KITCHEN_MANAGER_EMAIL,
        password=KITCHEN_MANAGER_PASSWORD,
        persona=Persona.KITCHEN_MANAGER.value,
    )
    fb_manager = seed_user(
        db,
        email=FB_MANAGER_EMAIL,
        password=FB_MANAGER_PASSWORD,
        persona=Persona.FB_MANAGER.value,
    )
    return kitchen_manager, fb_manager
