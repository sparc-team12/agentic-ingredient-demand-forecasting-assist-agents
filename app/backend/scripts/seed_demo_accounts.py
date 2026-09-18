"""Standalone CLI: create schema (if needed) and seed the 2 demo accounts.

Usage (from `app/backend`, with the venv activated):

    python -m scripts.seed_demo_accounts

Exposes the same idempotent `seed_demo_accounts` logic that also runs
automatically on backend startup (`main.py`), for explicit/manual invocation
(e.g. CI, a fresh environment) without starting the full ASGI app.
"""

from __future__ import annotations

import logging

from db.seed import seed_demo_accounts
from db.session import Base, SessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        created = seed_demo_accounts(db)
        if created:
            logger.info("Seeded %d demo account(s).", created)
        else:
            logger.info("Demo accounts already exist — no-op.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
