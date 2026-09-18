"""Idempotent demo-account seeding (ACRI-66).

Creates exactly the two demo accounts this story requires — one per persona
(kitchen-manager, fb-manager) — from env-configured, documented,
non-production-real credentials. Safe to call on every backend startup: a
no-op once the two accounts already exist (idempotent, checked by email).
"""

from __future__ import annotations

import logging
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Persona, User
from services.auth_service import hash_password

logger = logging.getLogger(__name__)

# Obviously-fake fallback values used only if the corresponding env var is
# unset (e.g. a fresh clone before `.env` is configured). Never real
# credentials — see the tech-lead review MINOR finding on this story.
_DEFAULT_KITCHEN_MANAGER_EMAIL = "kitchen.manager@example.com"
_DEFAULT_KITCHEN_MANAGER_PASSWORD = "changeme-not-a-real-secret"
_DEFAULT_FB_MANAGER_EMAIL = "fb.manager@example.com"
_DEFAULT_FB_MANAGER_PASSWORD = "changeme-also-not-a-real-secret"


def _demo_accounts() -> list[tuple[str, str, str]]:
    """Return the (email, password, persona) tuples to seed, from env vars."""
    return [
        (
            os.environ.get("SEED_KITCHEN_MANAGER_EMAIL", _DEFAULT_KITCHEN_MANAGER_EMAIL),
            os.environ.get("SEED_KITCHEN_MANAGER_PASSWORD", _DEFAULT_KITCHEN_MANAGER_PASSWORD),
            Persona.KITCHEN_MANAGER.value,
        ),
        (
            os.environ.get("SEED_FB_MANAGER_EMAIL", _DEFAULT_FB_MANAGER_EMAIL),
            os.environ.get("SEED_FB_MANAGER_PASSWORD", _DEFAULT_FB_MANAGER_PASSWORD),
            Persona.FB_MANAGER.value,
        ),
    ]


def seed_demo_accounts(db: Session) -> int:
    """Create the 2 documented demo accounts if they don't already exist.

    Idempotent: looked up by (lowercased) email; an existing account is left
    untouched on repeat calls (no password overwrite). Returns the number of
    accounts newly created (0 on a no-op run).
    """
    created = 0
    for email, password, persona in _demo_accounts():
        normalized_email = email.strip().lower()
        existing = db.execute(
            select(User).where(User.email == normalized_email)
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.add(
            User(
                email=normalized_email,
                password_hash=hash_password(password),
                persona=persona,
            )
        )
        created += 1
    if created:
        db.commit()
        logger.info("seed_demo_accounts", extra={"accounts_created": created})
    return created
